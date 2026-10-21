"""GET /api/zones (F7)."""
from pydantic import BaseModel, Field


class ZoneOut(BaseModel):
    """A municipality polygon colour-coded by tryghed."""

    id: str
    safety_score: float = Field(..., ge=1, le=10)
    safety_label: str  # 'unsafe' | 'mixed' | 'safe'
    geometry: dict  # GeoJSON Polygon / MultiPolygon
