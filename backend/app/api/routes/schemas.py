"""GET /api/routes (F1, NF1)."""
from pydantic import BaseModel, Field


class RouteOption(BaseModel):
    """A single candidate route: travel time + tryghedsscore."""

    duration_minutes: float
    distance_meters: float
    safety_score: float = Field(..., ge=1, le=10, description="1 = least safe, 10 = safest")
    safety_label: str  # 'not safe' | 'okay' | 'safe' | 'very safe'
    explanation: str = Field(..., description="Short text on what the score is based on (NF8)")
    geometry: dict  # GeoJSON LineString
