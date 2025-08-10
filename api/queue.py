import asyncio
from typing import Optional, Dict, cast

from flow.tts.gemini_voices import select_voice_by_name as select_gemini_voice
from flow.tts.elevenlabs_voices import select_voice_by_name as select_elevenlabs_voice
from flow.models.voices import Voice
from flow.utils.languages import select_language_by_name
from pipeline import run_pipeline
from .jobs import JobStore, JobResult, now_iso


class Worker:
    """
    Simple single-consumer queue worker:
      - Accepts job IDs
      - Pulls from asyncio.Queue
      - Runs pipeline in a thread to avoid blocking the event loop
    """
    def __init__(self, store: JobStore) -> None:
        self.store = store
        self.queue: "asyncio.Queue[str]" = asyncio.Queue()
        self._task: Optional[asyncio.Task] = None
        self._stop = asyncio.Event()

    async def start(self) -> None:
        self._stop.clear()
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self._run(), name="queue-worker")

    async def stop(self) -> None:
        self._stop.set()
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    async def enqueue(self, job_id: str) -> None:
        await self.queue.put(job_id)

    async def _run(self) -> None:
        while not self._stop.is_set():
            try:
                job_id = await self.queue.get()
            except asyncio.CancelledError:
                break
            try:
                await self._process(job_id)
            finally:
                self.queue.task_done()

    async def _process(self, job_id: str) -> None:
        job = self.store.get(job_id)
        if job is None:
            return  # unknown job (race or restart before load)

        # Transition to RUNNING
        self.store.update(job_id, status="RUNNING", started_at=now_iso(), error=None)

        # Resolve language (best-effort fuzzy)
        lang_code = job.params.target_language
        try:
            lang_code = select_language_by_name(job.params.target_language)
        except Exception:
            # keep whatever was supplied; pipeline will error if invalid
            pass

        # Resolve voice
        voice: Voice
        try:
            if job.params.tts_provider == "gemini":
                # default if not provided
                vname = job.params.voice_name or "Orus"
                voice = select_gemini_voice(vname)
            else:
                vname = job.params.voice_name or "Daniel"
                voice = select_elevenlabs_voice(vname)
        except Exception as e:
            self.store.update(
                job_id,
                status="FAILED",
                finished_at=now_iso(),
                error=f"Voice selection failed: {e}",
            )
            return

        # Heavy pipeline run (offloaded to a background thread)
        def _run_sync_pipeline() -> Dict[str, str]:
            paths = run_pipeline(
                video_url=job.params.yt_video_url,
                target_language=lang_code,
                voice=voice,
                original_audio_loudness=0.13,
            )
            # request_id is Optional[str] in the dataclass but guaranteed set in __post_init__
            req_id = cast(str, paths.request_id)

            # Flatten path properties for convenience in status/result
            return {
                "downloaded_video_path": paths.downloaded_video_path,
                "video_no_audio_path": paths.video_no_audio_path,
                "audio_no_video_path": paths.audio_no_video_path,
                "generated_cc_path": paths.generated_cc_path,
                "translated_cc_path": paths.translated_cc_path,
                "generated_narration_path": paths.generated_narration_path,
                "final_video_path": paths.final_video_path,
                "video_info_path": paths.video_info_path,
                "request_id": req_id,  # keep as string
            }

        try:
            # Use stdlib asyncio.to_thread for portability and to satisfy Pylance
            flattened = await asyncio.to_thread(_run_sync_pipeline)
            request_id = flattened.pop("request_id")
            result = JobResult(
                request_id=request_id,
                paths=flattened,
            )
            self.store.update(
                job_id,
                status="SUCCESS",
                finished_at=now_iso(),
                result=result,
                error=None,
            )
        except Exception as e:
            self.store.update(
                job_id,
                status="FAILED",
                finished_at=now_iso(),
                error=str(e),
            )
