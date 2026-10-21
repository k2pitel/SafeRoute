"""GET/POST /api/reports, POST /api/reports/{id}/confirm (F2, F3)."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ReportCreate(BaseModel):
    type: str  # e.g. 'harassment' | 'assault' | 'theft' | 'suspicious' | 'other'
    latitude: float
    longitude: float
    description: str | None = None
    occurred_at: datetime | None = None  # defaults to now if omitted


class ReportOut(BaseModel):
    """Deliberately has no ``user_id``: who submitted a report is never
    sent to other users (NF11)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    type: str
    latitude: float
    longitude: float
    description: str | None = None
    occurred_at: datetime
    confirmations: int
    created_at: datetime
