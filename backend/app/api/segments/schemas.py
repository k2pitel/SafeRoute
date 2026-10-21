"""GET /api/segments/{id}/explain (NF8)."""
from pydantic import BaseModel


class SegmentExplanation(BaseModel):
    segment_id: str
    safety_score: float
    top_features: list[dict]  # e.g. [{"feature": "recent_incidents_7d", "impact": 0.42}, ...]
