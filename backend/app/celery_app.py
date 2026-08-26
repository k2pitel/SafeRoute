"""Celery application instance — imports task modules so they get registered."""
from celery import Celery

from app.config import settings

celery_app = Celery("saferoute", broker=settings.redis_url, backend=settings.redis_url)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "recalculate-segment-scores": {
            "task": "app.tasks.recalculate_segment_scores",
            "schedule": 900.0,  # every 15 minutes
        },
        "ingest-news": {
            "task": "app.tasks.ingest_news",
            "schedule": 1800.0,  # every 30 minutes
        },
    },
)

import app.tasks  # noqa: E402,F401  (registers tasks with the app)
