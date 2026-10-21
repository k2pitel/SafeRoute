"""Celery application — target-architecture Async Worker (afsnit 4.3.4.5).

Started as its own container (infra/docker/worker.Dockerfile):
    celery -A app.worker.celery_app worker --beat -l info
The Beat schedule mirrors the launch variant's intervals (worker/base.py).
"""
from celery import Celery

from app.config import settings
from app.worker.base import (
    CRIME_STATS_REFRESH_INTERVAL_SECONDS,
    NEWS_POLL_INTERVAL_SECONDS,
    SEGMENT_SCORE_INTERVAL_SECONDS,
)

celery_app = Celery("saferoute", broker=settings.redis_url, backend=settings.redis_url)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "recalculate-segment-scores": {
            "task": "app.worker.tasks.recalculate_segment_scores",
            "schedule": float(SEGMENT_SCORE_INTERVAL_SECONDS),
        },
        "ingest-news": {
            "task": "app.worker.tasks.ingest_news",
            "schedule": float(NEWS_POLL_INTERVAL_SECONDS),
        },
        "refresh-crime-stats": {
            "task": "app.worker.tasks.refresh_crime_stats",
            "schedule": float(CRIME_STATS_REFRESH_INTERVAL_SECONDS),
        },
    },
)

import app.worker.tasks  # noqa: F401  (registers tasks with the app)
