import requests
import time
import sys

BASE_URL = "http://127.0.0.1:8000"

# --- configuration for the test run ---
TEST_PAYLOAD = {
    "yt_video_url": "https://www.youtube.com/watch?v=tqPQB5sleHY",
    "target_language": "Polish",
    "tts_provider": "elevenlabs",
    "voice_name": "Daniel"
}
POLL_INTERVAL = 5  # seconds


def enqueue_job() -> str:
    """POST to /renarrate and return the job_id."""
    url = f"{BASE_URL}/renarrate"
    print(f"Enqueuing job at {url} ...")
    resp = requests.post(url, json=TEST_PAYLOAD)
    if resp.status_code != 202:
        print(f"Error: {resp.status_code} {resp.text}")
        sys.exit(1)
    data = resp.json()
    print(f"Enqueued job_id={data['job_id']}, initial status={data['status']}")
    return data["job_id"]


def poll_status(job_id: str) -> dict:
    """Poll /status/{job_id} until terminal state reached."""
    url = f"{BASE_URL}/status/{job_id}"
    while True:
        resp = requests.get(url)
        if resp.status_code != 200:
            print(f"Error: {resp.status_code} {resp.text}")
            sys.exit(1)
        job = resp.json()["job"]
        status = job["status"]
        print(f"[{time.strftime('%H:%M:%S')}] Job {job_id} status: {status}")
        if status in ("SUCCESS", "FAILED"):
            return job
        time.sleep(POLL_INTERVAL)


def main():
    job_id = enqueue_job()
    final_job = poll_status(job_id)
    print("\nFinal job record:")
    print(final_job)


if __name__ == "__main__":
    main()
