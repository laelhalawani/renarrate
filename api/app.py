from contextlib import asynccontextmanager
from typing import Dict, Any, Optional, List
import json
import os

from fastapi import FastAPI, status, HTTPException, Query
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from .schemas import RenarrateRequest, EnqueueResponse, StatusResponse
from .jobs import JobStore, JobParams
from .queue import Worker


# Global singletons for dev host mode (single process)
job_store = JobStore(persist=True)
worker = Worker(store=job_store)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    job_store.load()
    await worker.start()
    try:
        yield
    finally:
        # Shutdown
        await worker.stop()
        job_store.dump()


app = FastAPI(
    title="Renarration Pipeline API",
    version="0.3.1",
    lifespan=lifespan,
)

# --------------------
# Job creation & status
# --------------------

@app.post(
    "/renarrate",
    response_model=EnqueueResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Enqueue a renarration job",
    tags=["jobs"],
)
async def post_renarrate(body: RenarrateRequest):
    params = JobParams(
        yt_video_url=str(body.yt_video_url),
        target_language=body.target_language,
        tts_provider=body.tts_provider,
        voice_name=body.voice_name,
    )
    job = job_store.create(params)
    await worker.enqueue(job.id)
    return EnqueueResponse(job_id=job.id, status="PENDING")


@app.get(
    "/status/{job_id}",
    response_model=StatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get job status",
    tags=["jobs"],
)
async def get_status(job_id: str):
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return StatusResponse(job=job.to_public_dict())


# -------------
# Helper methods
# -------------

def _ensure_success_and_get_paths(job_id: str) -> Dict[str, str]:
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != "SUCCESS":
        raise HTTPException(
            status_code=409,
            detail=f"Job not ready: status={job.status}. Try again later.",
        )
    if not job.result or not job.result.paths:
        raise HTTPException(status_code=500, detail="Job result missing paths.")
    return job.result.paths


# -----------------
# Retrieval endpoints
# -----------------

@app.get(
    "/video_info/{job_id}",
    status_code=status.HTTP_200_OK,
    summary="Return extracted video metadata (info.json)",
    tags=["artifacts"],
)
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


@app.get(
    "/video/{job_id}",
    status_code=status.HTTP_200_OK,
    summary="Download the final video artifact",
    tags=["artifacts"],
)
async def get_video(job_id: str):
    paths = _ensure_success_and_get_paths(job_id)
    video_path = paths.get("final_video_path")
    if not video_path or not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail="Final video not found.")

    # Guess media type by extension (simple dev heuristic)
    _, ext = os.path.splitext(video_path.lower())
    media_type = (
        "video/mp4" if ext == ".mp4"
        else "video/webm" if ext == ".webm"
        else "video/x-matroska" if ext == ".mkv"
        else "application/octet-stream"
    )

    return FileResponse(path=video_path, media_type=media_type, filename=os.path.basename(video_path))


# ------------------------
# Listing endpoint for UI
# ------------------------

@app.get(
    "/jobs",
    status_code=status.HTTP_200_OK,
    summary="List jobs (optionally filter by status). Used by the web UI.",
    tags=["jobs"],
)
async def list_jobs(status_filter: Optional[str] = Query(None, alias="status")):
    """
    Returns a light list for the left column:
    [
      {
        "job_id": "...",
        "status": "SUCCESS",
        "title": "Video Title",
        "request_id": "...",
        "video_url": "/video/{job_id}",
        "info_url": "/video_info/{job_id}"
      },
      ...
    ]
    """
    items: List[Dict[str, Any]] = []
    # Iterate deterministically by submit time
    jobs = list(job_store._jobs.values())  # dev-only direct access for listing
    jobs.sort(key=lambda j: j.submitted_at)

    for j in jobs:
        if status_filter and j.status != status_filter:
            continue
        title = None
        req_id = None
        if j.status == "SUCCESS" and j.result and j.result.paths:
            req_id = j.result.request_id
            info_path = j.result.paths.get("video_info_path")
            if info_path and os.path.exists(info_path):
                try:
                    with open(info_path, "r", encoding="utf-8") as f:
                        info = json.load(f)
                        title = info.get("title")
                except Exception:
                    title = None

        items.append({
            "job_id": j.id,
            "status": j.status,
            "title": title,
            "request_id": req_id,
            "video_url": f"/video/{j.id}",
            "info_url": f"/video_info/{j.id}",
        })
    return {"jobs": items}


# --- Static site (served at "/") ---
# IMPORTANT: mount AFTER routes so API endpoints take precedence.
app.mount("/", StaticFiles(directory="web", html=True), name="web")


# Optional: run with `python -m api.app` for quick dev
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.app:app", host="127.0.0.1", port=8000, reload=True)
