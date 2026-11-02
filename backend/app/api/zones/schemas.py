"""GET /api/zones (F7)."""
from pydantic import BaseModel, Field


class ZoneOut(BaseModel):
    """A municipality polygon colour-coded by tryghed, with what the colour
    is based on (US-20: tap a zone to see why)."""

    id: str
    name: str
    safety_score: float = Field(..., ge=1, le=10)
    safety_label: str  # 'unsafe' | 'mixed' | 'safe'
    crime_rate_per_100k: float
    national_rate_per_100k: float
    data_period: str | None = None  # e.g. "2025K3-2026K2" (DP-07)
    geometry: dict  # GeoJSON Polygon / MultiPolygon, simplified for display
