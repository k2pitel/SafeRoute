"""GET /api/segments/{id}/explain — SHAP-based explanation for a segment score."""
from fastapi import APIRouter

from app.schemas import SegmentExplanation

router = APIRouter(prefix="/api/segments", tags=["segments"])


@router.get("/{segment_id}/explain", response_model=SegmentExplanation)
def explain_segment(segment_id: str):
    """
    NOTE: stub. In production this loads the SHAP values stored alongside
    the segment's latest score (see `segment_scores.shap_summary` in the
    DB schema) rather than recomputing them per-request.
    """
    return SegmentExplanation(
        segment_id=segment_id,
        safety_score=6.8,
        top_features=[
            {"feature": "recent_incidents_7d", "impact": 0.42},
            {"feature": "street_lighting", "impact": -0.31},
            {"feature": "time_of_day_night", "impact": 0.18},
            {"feature": "pedestrian_density", "impact": -0.09},
        ],
    )
