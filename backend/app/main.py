"""SafeRoute backend — FastAPI application entrypoint.

Run locally with:
    uvicorn app.main:app --reload
"""
import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import crime_stats, news_archive
from app.routers import crime_index, incidents, news, reports, routes, segments, zones

logger = logging.getLogger("saferoute.news_poller")

NEWS_POLL_INTERVAL_SECONDS = 15 * 60  # 15 minutes
CRIME_STATS_REFRESH_INTERVAL_SECONDS = 6 * 60 * 60  # 6 hours — official stats only change quarterly


async def _news_poll_loop():
    """
    Background "bot": periodically re-fetches every configured news feed
    and archives anything new — see news_archive.py for why (RSS has no
    memory of its own, so this is what lets the app accumulate real
    history over time instead of only ever seeing the last ~2 days).
    """
    while True:
        try:
            new_count = await news.poll_and_archive_once()
            if new_count:
                logger.info("news poller: archived %d new item(s)", new_count)
        except Exception:
            logger.exception("news poller: fetch failed, will retry next interval")
        await asyncio.sleep(NEWS_POLL_INTERVAL_SECONDS)


async def _crime_stats_refresh_loop():
    """Real municipality-level crime-rate data — see app/crime_stats.py."""
    while True:
        try:
            await crime_stats.refresh_cache()
        except Exception:
            logger.exception("crime_stats: refresh failed, will retry next interval")
        await asyncio.sleep(CRIME_STATS_REFRESH_INTERVAL_SECONDS)


@asynccontextmanager
async def lifespan(app: FastAPI):
    news_archive.init_db()
    poll_task = asyncio.create_task(_news_poll_loop())
    stats_task = asyncio.create_task(_crime_stats_refresh_loop())
    yield
    poll_task.cancel()
    stats_task.cancel()


app = FastAPI(
    title="SafeRoute API",
    description="Safety-aware pedestrian navigation backend.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten before production
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(incidents.router)
app.include_router(routes.router)
app.include_router(reports.router)
app.include_router(crime_index.router)
app.include_router(news.router)
app.include_router(segments.router)
app.include_router(zones.router)


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok"}
