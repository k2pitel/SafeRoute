"""GET /api/segments/{id}/explain — the explanation behind a segment's score (NF8)."""
from fastapi import APIRouter

from app.api.segments import service as segments
from app.api.segments.schemas import SegmentExplanation

router = APIRouter(prefix="/api/segments", tags=["segments"])


@router.get("/{segment_id}/explain", response_model=SegmentExplanation)
def explain_segment(segment_id: str):
    return segments.explain_segment(segment_id)
