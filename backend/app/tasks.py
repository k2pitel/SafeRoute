"""Celery background tasks — score recalculation, news ingestion, etc."""
import logging

from app.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.recalculate_segment_scores")
def recalculate_segment_scores():
    """
    Recompute `segment_scores` from the latest incidents/reports/news.

    NOTE: stub. Real implementation should:
      1. Pull recent incidents/reports/news from the DB.
      2. Build features per road segment (see ml/features.py).
      3. Run the trained model (ml/serving) to get a score + SHAP values.
      4. Upsert into `segment_scores`, then publish a change event to
         Redis pub/sub so `/ws/zones` can push it to connected clients.
    """
    logger.info("recalculate_segment_scores: stub run")


@celery_app.task(name="app.tasks.ingest_news")
def ingest_news():
    """
    Poll configured news sources, filter for crime relevance, and cache
    results for the /api/news endpoint.

    NOTE: stub — wire up a real news API/RSS client + classifier.
    """
    logger.info("ingest_news: stub run")
