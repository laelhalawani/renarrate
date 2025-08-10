from contextlib import asynccontextmanager
from typing import Dict, Any, Optional, List
import json
import os
import shutil

from fastapi import FastAPI, status, HTTPException, Query, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .schemas import RenarrateRequest, EnqueueResponse, StatusResponse
from .jobs import JobStore, JobParams, JobResult, now_iso
from settings import STORAGE_DIR

from celery.result import AsyncResult
from worker.celery_app import celery
from worker.tasks import run_pipeline_task

from fastapi.middleware.cors import CORSMiddleware

# Persist a job list for the web UI (lightweight index)
job_store = JobStore(persist=True)



@asynccontextmanager
async def lifespan(app: FastAPI):
    job_store.load()
    yield
    job_store.dump()

app = FastAPI(
    title="Renarration Pipeline API (Celery mode)",
    version="1.1.2",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten later if you want
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
# --------------------
# Job creation & status
# --------------------

@app.post(
    "/renarrate",
    response_model=EnqueueResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Enqueue a renarration job (Celery)",
    tags=["jobs"],
)
async def post_renarrate(body: RenarrateRequest):
    task = run_pipeline_task.delay(
        yt_video_url=str(body.yt_video_url),
        target_language=body.target_language,
        tts_provider=body.tts_provider,
        voice_name=body.voice_name,
    )
    params = JobParams(
        yt_video_url=str(body.yt_video_url),
        target_language=body.target_language,
        tts_provider=body.tts_provider,
        voice_name=body.voice_name,
    )
    job_store.create(params, job_id=task.id)
    return EnqueueResponse(job_id=task.id, status="PENDING")


def _map_celery_state_to_status(state: str) -> str:
    if state in ("PENDING", "RETRY"):
        return "PENDING"
    if state == "STARTED":
        return "RUNNING"
    if state == "SUCCESS":
        return "SUCCESS"
    if state in ("FAILURE", "REVOKED"):
        return "FAILED"
    return "PENDING"


@app.get(
    "/status/{job_id}",
    response_model=StatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get job status (Celery)",
    tags=["jobs"],
)
async def get_status(job_id: str):
    res = AsyncResult(job_id, app=celery)
    status_mapped = _map_celery_state_to_status(res.state)

    job = job_store.get(job_id)
    if job:
        patch: Dict[str, Any] = {"status": status_mapped}
        if status_mapped == "RUNNING" and not job.started_at:
            patch["started_at"] = now_iso()
        if status_mapped in ("SUCCESS", "FAILED") and not job.finished_at:
            patch["finished_at"] = now_iso()

        if status_mapped == "SUCCESS" and res.result:
            try:
                payload: Dict[str, str] = dict(res.result)
                request_id = payload.pop("request_id", None)
                jr = JobResult(request_id=request_id, paths=payload)
                patch["result"] = jr
                patch["error"] = None
            except Exception as e:
                patch["error"] = f"Bad result payload: {e}"

        if status_mapped == "FAILED" and res.result:
            try:
                patch["error"] = str(res.result)
            except Exception:
                patch["error"] = "Task failed."

        job_store.update(job_id, **patch)

    job = job_store.get(job_id)
    if job:
        return StatusResponse(job=job.to_public_dict())
    else:
        return StatusResponse(job={"id": job_id, "status": status_mapped})

# -------------
# Helper methods
# -------------

def _ensure_success_and_get_paths(job_id: str) -> Dict[str, str]:
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    res = AsyncResult(job_id, app=celery)
    status_mapped = _map_celery_state_to_status(res.state)
    if status_mapped != "SUCCESS":
        raise HTTPException(
            status_code=409,
            detail=f"Job not ready: status={status_mapped}. Try again later.",
        )

    if not job.result or not job.result.paths:
        try:
            payload: Dict[str, str] = dict(res.result)
            request_id = payload.pop("request_id", None)
            jr = JobResult(request_id=request_id, paths=payload)
            job_store.update(job_id, result=jr)
        except Exception:
            pass

    job = job_store.get(job_id)
    if not job or not job.result or not job.result.paths:
        raise HTTPException(status_code=500, detail="Job result missing paths.")
    return job.result.paths  # type: ignore[return-value]


# -----------------
# Retrieval endpoints
# -----------------

@app.get("/video_info/{job_id}", tags=["artifacts"])
async def get_video_info(job_id: str):
    paths = _ensure_success_and_get_paths(job_id)
    info_path = paths.get("video_info_path")
    if not info_path or not os.path.exists(info_path):
        raise HTTPException(status_code=404, detail="Video info not found.")
    try:
        with open(info_path, "r", encoding="utf-8") as f:
            info = json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read info.json: {e}")
    return {"job_id": job_id, "video_info": info}


@app.get("/video/{job_id}", tags=["artifacts"])
async def get_video(job_id: str):
    paths = _ensure_success_and_get_paths(job_id)
    video_path = paths.get("final_video_path")
    if not video_path or not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail="Final video not found.")
    _, ext = os.path.splitext(video_path.lower())
    media_type = (
        "video/webm" if ext == ".webm"
        else "video/mp4" if ext == ".mp4"
        else "video/x-matroska" if ext == ".mkv"
        else "application/octet-stream"
    )
    return FileResponse(path=video_path, media_type=media_type, filename=os.path.basename(video_path))


# ------------------------
# Listing endpoint for UI (self-hydrates from Celery) + no-cache
# ------------------------

@app.get("/jobs", tags=["jobs"])
async def list_jobs(response: Response, status_filter: Optional[str] = Query(None, alias="status")):
    # Make sure browsers never cache this
    response.headers["Cache-Control"] = "no-store, max-age=0"

    items: List[Dict[str, Any]] = []
    jobs = list(job_store._jobs.values())  # dev-only direct access for listing
    jobs.sort(key=lambda j: j.submitted_at)

    for j in jobs:
        if status_filter and j.status != status_filter:
            continue

        # Hydrate result from Celery if missing
        if not (j.result and j.result.paths):
            res = AsyncResult(j.id, app=celery)
            if _map_celery_state_to_status(res.state) == "SUCCESS" and res.result:
                try:
                    payload: Dict[str, str] = dict(res.result)
                    request_id = payload.pop("request_id", None)
                    jr = JobResult(request_id=request_id, paths=payload)
                    job_store.update(j.id, result=jr, status="SUCCESS", finished_at=now_iso())
                except Exception:
                    pass

        # After hydration, attempt to read title
        title = None
        req_id = None
        jj = job_store.get(j.id)
        if jj and jj.result and jj.result.paths:
            req_id = jj.result.request_id
            info_path = jj.result.paths.get("video_info_path")
            if info_path and os.path.exists(info_path):
                try:
                    with open(info_path, "r", encoding="utf-8") as f:
                        info = json.load(f)
                        title = info.get("title")
                except Exception:
                    title = None

        items.append({
            "job_id": j.id,
            "status": (jj.status if jj else j.status),
            "title": title,
            "request_id": req_id,
            "video_url": f"/video/{j.id}",
            "info_url": f"/video_info/{j.id}",
        })
    return {"jobs": items}

# ------------------------
# Dev-only reset endpoint
# ------------------------

@app.post("/admin/clear", tags=["admin"])
async def admin_clear(artifacts: bool = False):
    """
    Clear in-memory jobs and delete storage/jobs.json.
    If artifacts=True, also delete all job subfolders under storage/.
    """
    # wipe memory
    cleared = len(job_store._jobs)
    job_store._jobs.clear()

    # wipe jobs.json
    jobs_path = os.path.join(STORAGE_DIR, "jobs.json")
    try:
        if os.path.exists(jobs_path):
            os.remove(jobs_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to remove jobs.json: {e}")

    # optionally wipe all artifacts
    removed_dirs = 0
    if artifacts:
        try:
            for name in os.listdir(STORAGE_DIR):
                p = os.path.join(STORAGE_DIR, name)
                if os.path.isdir(p):
                    shutil.rmtree(p, ignore_errors=True)
                    removed_dirs += 1
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to clear artifacts: {e}")

    return {"cleared_in_memory": cleared, "deleted_artifact_dirs": removed_dirs}

# --- Static site (served at "/") ---
app.mount("/", StaticFiles(directory="web", html=True), name="web")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.app_celery:app", host="0.0.0.0", port=8000)
