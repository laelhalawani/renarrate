import json
import os
import uuid
from datetime import datetime, timezone
from typing import Dict, Optional, Literal, Any, TypedDict

from pydantic import BaseModel, Field

from settings import STORAGE_DIR

JobStatus = Literal["PENDING", "RUNNING", "SUCCESS", "FAILED"]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class JobParams(BaseModel):
    yt_video_url: str
    target_language: str
    tts_provider: Literal["elevenlabs", "gemini"]
    voice_name: Optional[str] = None


class JobResult(BaseModel):
    request_id: Optional[str] = None
    paths: Optional[Dict[str, str]] = None  # flattened absolute paths for convenience


class Job(BaseModel):
    id: str
    status: JobStatus = "PENDING"
    submitted_at: str = Field(default_factory=now_iso)
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    params: JobParams
    result: Optional[JobResult] = None
    error: Optional[str] = None

    def to_public_dict(self) -> Dict[str, Any]:
        return self.model_dump()


class _DumpModel(TypedDict, total=False):
    jobs: Dict[str, Dict[str, Any]]


class JobStore:
    """
    In-memory job registry with optional JSON persistence under storage/jobs.json.
    NOTE: Single-process dev only. For multi-process/containers, we'll move to Redis.
    """
    def __init__(self, persist: bool = True) -> None:
        self._jobs: Dict[str, Job] = {}
        self._persist = persist
        self._path = os.path.join(STORAGE_DIR, "jobs.json")
        os.makedirs(STORAGE_DIR, exist_ok=True)

    # basic CRUD

    def create(self, params: JobParams, job_id: Optional[str] = None) -> Job:
        """
        Create a job record. If job_id is provided (e.g., Celery task id),
        it will be used as the key and Job.id. Otherwise a UUID4 is generated.
        """
        jid = job_id or str(uuid.uuid4())
        job = Job(id=jid, params=params)
        self._jobs[jid] = job
        self._dump_if_enabled()
        return job

    def get(self, job_id: str) -> Optional[Job]:
        return self._jobs.get(job_id)

    def update(self, job_id: str, **patch: Any) -> Optional[Job]:
        job = self._jobs.get(job_id)
        if not job:
            return None
        updated = job.model_copy(update=patch)
        self._jobs[job_id] = updated
        self._dump_if_enabled()
        return updated

    # persistence

    def load(self) -> None:
        if not self._persist:
            return
        try:
            if os.path.exists(self._path):
                with open(self._path, "r", encoding="utf-8") as f:
                    raw: _DumpModel = json.load(f)
                self._jobs = {jid: Job(**payload) for jid, payload in raw.get("jobs", {}).items()}
        except Exception:
            self._jobs = {}

    def dump(self) -> None:
        if not self._persist:
            return
        self._dump_if_enabled()

    def _dump_if_enabled(self) -> None:
        if not self._persist:
            return
        data: _DumpModel = {"jobs": {jid: j.model_dump() for jid, j in self._jobs.items()}}
        tmp = self._path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, self._path)
