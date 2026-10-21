"""Celery tasks — thin wrappers that run the shared jobs (worker/jobs.py).

Celery workers are synchronous, so each task drives its async job with
asyncio.run. Retry/backoff policy belongs here, not in the jobs.

Note: in this realisation zone_updates events are published inside the
Celery process; reaching /ws/zones subscribers in the API process needs the
broker's Redis pub/sub behind api/zones/updates.py.
"""
import asyncio
import logging

from app.shared.geo import BBox
from app.worker import jobs
from app.worker.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="app.worker.tasks.recalculate_segment_scores")
def recalculate_segment_scores(area: list[float] | None = None):
    asyncio.run(jobs.recalculate_segment_scores(BBox(*area) if area else None))


@celery_app.task(name="app.worker.tasks.ingest_news")
def ingest_news():
    return asyncio.run(jobs.poll_news())


@celery_app.task(name="app.worker.tasks.refresh_crime_stats")
def refresh_crime_stats():
    return asyncio.run(jobs.refresh_crime_stats())
