"""The Async Worker's jobs — one function per job, independent of how they're scheduled.

Every job catches nothing itself; the realisation running it decides
retry behaviour (the background worker logs and retries next interval,
Celery has its own retry policy). That keeps a failing external source
from ever stopping the Backend API (NF7).
"""
import logging
from datetime import UTC, datetime

from app.api.auth import service as auth
from app.api.crime_index import world as world_safety
from app.api.news import service as news
from app.api.zones import crime_stats
from app.api.zones import updates as zone_updates
from app.shared.geo import BBox

logger = logging.getLogger("saferoute.worker")


async def poll_news() -> int:
    """Fetch, place and archive new crime news (every 15 min)."""
    new_count = await news.poll_and_archive_once()
    if new_count:
        logger.info("poll_news: archived %d new item(s)", new_count)
    return new_count


async def refresh_crime_stats() -> int:
    """Rebuild the zone cache from Danmarks Statistik (every 6 h) and tell
    /ws/zones subscribers the zones changed."""
    cached = await crime_stats.refresh_cache()
    zone_updates.publish({
        "type": "zones_refreshed",
        "zones_cached": cached,
        "updated_at": datetime.now(UTC).isoformat(),
    })
    return cached


async def recalculate_segment_scores(area: BBox | None = None) -> None:
    """Recompute ``segment_scores`` — for one area when event-triggered by a
    newly verified report (NF5), or everywhere on the periodic run.

    NOTE: stub. The pipeline this must implement (afsnit 4.2.1, 4.2.4):
      1. load incidents + verified reports + news for the area (Datalag),
      2. build features per segment (worker/scoring/features.py),
      3. score with the model + SHAP explanation (worker/scoring/serving.py),
      4. add differential-privacy noise HERE, once, at write time
         (worker/scoring/laplace.py, ε = settings.dp_epsilon) — never per read,
         which would allow an averaging attack (afsnit 4.2.4),
      5. upsert into ``segment_scores`` and publish a zone_updates event.
    """
    logger.info("recalculate_segment_scores: stub run for %s", area or "all areas")


async def purge_expired_reports() -> int:
    """US-59 retention: delete reports older than settings.report_retention_days (daily)."""
    removed = auth.purge_expired_reports()
    if removed:
        logger.info("purge_expired_reports: deleted %d report(s)", removed)
    return removed


async def relocate_news() -> int:
    """US-28: re-place archived articles with the current gazetteer (districts
    beat cities). Cheap regex work; daily, so gazetteer fixes reach old items."""
    moved = news.relocate_archive()
    if moved:
        logger.info("relocate_news: moved %d archived article(s)", moved)
    return moved


async def refresh_world_safety() -> int:
    """Country and European-city safety data from Eurostat and the World Bank
    (daily; the sources publish yearly). Keeps the old data on failure (NF7)."""
    return await world_safety.refresh_cache()
