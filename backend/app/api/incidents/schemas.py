"""GET /api/incidents."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class IncidentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: str
    description: str | None = None
    latitude: float
    longitude: float
    occurred_at: datetime
    source: str  # 'official' | 'community' | 'news'
    verified: bool
