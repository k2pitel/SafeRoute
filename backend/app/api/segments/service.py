"""Explanation behind a segment's tryghedsscore (NF8).

NOTE: stub with fixed values. In the target design the SHAP values are
computed once by the Async Worker's scoring pipeline and stored with the
score (``segment_scores.shap_summary``), so this becomes a lookup, never a
per-request recomputation.
"""
from app.api.segments.schemas import SegmentExplanation


def explain_segment(segment_id: str) -> SegmentExplanation:
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
