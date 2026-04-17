from celery import Celery
import os
from app.core.config import config


celery_app = Celery(
    "worker",
    broker=config.redis_url,
    backend=config.redis_url,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    # Retry tasks that were in queue during a crash
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)