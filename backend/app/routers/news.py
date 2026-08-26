"""GET /api/news — latest crime-related news for a city."""
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Query

from app.schemas import NewsItem

router = APIRouter(prefix="/api/news", tags=["news"])


@router.get("", response_model=list[NewsItem])
def get_news(city: str = Query(...)):
    """
    NOTE: stub. In production this is populated by a Celery task that polls
    news APIs/RSS feeds, filters for crime-relevance (keyword/NLP classifier),
    and caches results per city — see README > Data Sources.
    """
    now = datetime.now(timezone.utc)
    return [
        NewsItem(
            title=f"Police increase patrols in central {city} after recent incidents",
            url="https://example.com/news/1",
            source="Local News Example",
            published_at=now - timedelta(hours=6),
            summary="Local authorities respond to a rise in reported incidents downtown.",
        ),
        NewsItem(
            title=f"{city} council to review street lighting in high-report areas",
            url="https://example.com/news/2",
            source="Local News Example",
            published_at=now - timedelta(days=1),
            summary="Proposal follows community feedback collected via safety apps.",
        ),
    ]
