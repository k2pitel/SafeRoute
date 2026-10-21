"""GET /api/news — crime-related news for Denmark, optionally per city or year (F9)."""
from fastapi import APIRouter, BackgroundTasks, Query

from app.api.news import backfill as news_backfill
from app.api.news import service as news
from app.shared.news import NewsItem

router = APIRouter(prefix="/api/news", tags=["news"])


@router.get("", response_model=list[NewsItem])
async def get_news(
    city: str = Query(None, description="Optional city filter; omit for all of Denmark"),
    year: int = Query(None, description="Optional year filter (e.g. 2020) — archive only, no live fetch"),
):
    return await news.get_news(city, year)


@router.get("/archive-status")
def archive_status():
    """How many crime items the Async Worker has archived so far."""
    return {"archived_count": news.archived_count()}


@router.post("/backfill")
async def trigger_backfill(background_tasks: BackgroundTasks):
    """One-time historical import from the Wayback Machine (api/news/backfill.py).
    Runs in the background since it makes several sequential requests to a
    free public archive; poll /api/news/archive-status to watch the count grow."""
    background_tasks.add_task(news_backfill.run_backfill)
    return {"status": "started", "note": "poll GET /api/news/archive-status for progress"}
