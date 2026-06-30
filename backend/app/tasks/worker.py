"""Celery worker configuration for async audio processing tasks."""

from celery import Celery

from app.core.config import settings

worker = Celery(
    "audio_ai",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

worker.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,  # 10 minutes max per task
    worker_max_memory_per_child=2000000,  # 2GB memory limit per worker
)
