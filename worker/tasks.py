import os
from typing import Dict

from worker.celery_app import celery
from flow.tts.gemini_voices import select_voice_by_name as select_gemini_voice
from flow.tts.elevenlabs_voices import select_voice_by_name as select_elevenlabs_voice
from flow.models.voices import Voice
from flow.utils.languages import select_language_by_name
from pipeline import run_pipeline

# The task returns a dict with request_id and all output paths (same shape used in host mode)
@celery.task(name="worker.tasks.run_pipeline_task", bind=True)
def run_pipeline_task(self, *, yt_video_url: str, target_language: str, tts_provider: str, voice_name: str | None) -> Dict[str, str]:
    # Resolve language (fuzzy by name)
    try:
        target_language = select_language_by_name(target_language)
    except Exception:
        # leave as-is; pipeline may raise if invalid
        pass

    # Resolve voice by provider
    if tts_provider == "gemini":
        voice = select_gemini_voice(voice_name or "Orus")
    else:
        voice = select_elevenlabs_voice(voice_name or "Daniel")

    # Run the pipeline
    paths = run_pipeline(
        video_url=yt_video_url,
        target_language=target_language,
        voice=voice,
        original_audio_loudness=0.13,
    )

    # Flatten paths for API convenience
    return {
        "downloaded_video_path": paths.downloaded_video_path,
        "video_no_audio_path": paths.video_no_audio_path,
        "audio_no_video_path": paths.audio_no_video_path,
        "generated_cc_path": paths.generated_cc_path,
        "translated_cc_path": paths.translated_cc_path,
        "generated_narration_path": paths.generated_narration_path,
        "final_video_path": paths.final_video_path,
        "video_info_path": paths.video_info_path,
        "request_id": paths.request_id or "",
    }
