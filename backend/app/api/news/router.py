"""GET /api/news — crime-related news for Denmark, optionally per city or year (F9)."""
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query

from app.api.dependencies import require_admin
from app.api.news import backfill as news_backfill
from app.api.news import service as news
from app.shared.news import NewsItem

router = APIRouter(prefix="/api/news", tags=["news"])


@router.get("", response_model=list[NewsItem])
async def get_news(
    city: str = Query(None, description="Optional city filter; omit for all of Denmark"),
    year: int = Query(None, description="Optional year filter (e.g. 2020) — archive only, no live fetch"),
    from_year: int | None = Query(None, alias="from", description="First year of a date range, e.g. 2024"),
    to_year: int | None = Query(None, alias="to", description="Last year of a date range, e.g. 2025"),
    located: bool = Query(False, description="Only items placed on the map (for map pins)"),
):
    """Latest (default), one ``year``, or a ``from``–``to`` range of years."""
    if from_year is not None or to_year is not None:
        lo, hi = from_year or to_year, to_year or from_year
        if lo > hi:
            raise HTTPException(status_code=422, detail="'from' must be before or equal to 'to'")
        return await news.get_news_range(city, lo, hi, located_only=located)
    return await news.get_news(city, year)


@router.get("/years")
def news_years():
    """First and last year in the archive, for the date-range filter."""
    return news.year_span() or {"min_year": None, "max_year": None}


@router.get("/archive-status")
def archive_status():
    """How many crime items the Async Worker has archived so far."""
    return {"archived_count": news.archived_count()}


@router.post("/backfill", dependencies=[Depends(require_admin)])
async def trigger_backfill(background_tasks: BackgroundTasks):
    """One-time historical import from the Wayback Machine (api/news/backfill.py).
    Runs in the background since it makes several sequential requests to a
    free public archive; poll /api/news/archive-status to watch the count grow."""
    background_tasks.add_task(news_backfill.run_backfill)
    return {"status": "started", "note": "poll GET /api/news/archive-status for progress"}
