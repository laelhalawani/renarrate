import os
from celery import Celery

# Broker / backend default to the compose service "redis"
BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/1")

# Explicitly include our tasks module so the worker registers tasks on boot.
celery = Celery(
    "renarrate",
    broker=BROKER_URL,
    backend=RESULT_BACKEND,
    include=["worker.tasks"],  # <-- ensure registration
)

# A few sensible defaults
celery.conf.update(
    task_routes={"worker.tasks.run_pipeline_task": {"queue": "pipeline"}},
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True,   # exposes STARTED state
    worker_send_task_events=True,
    task_send_sent_event=True,
    timezone="UTC",
    # Optional: silence future deprecation warning seen in your logs
    broker_connection_retry_on_startup=True,
)
