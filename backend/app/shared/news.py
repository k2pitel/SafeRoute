"""GET /api/news (F9)."""
from datetime import datetime

from pydantic import BaseModel


class NewsItem(BaseModel):
    title: str
    url: str
    source: str
    published_at: datetime
    summary: str | None = None
    latitude: float | None = None
    longitude: float | None = None
