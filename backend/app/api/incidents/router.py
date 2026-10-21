"""GET /api/incidents — incidents within a map bounding box."""
from fastapi import APIRouter, Depends, Query

from app.api.dependencies import bbox_query
from app.api.incidents import service as incidents
from app.api.incidents.schemas import IncidentOut
from app.shared.geo import BBox

router = APIRouter(prefix="/api/incidents", tags=["incidents"])


@router.get("", response_model=list[IncidentOut])
def list_incidents(bbox: BBox = Depends(bbox_query), limit: int = Query(100, le=500)):
    return incidents.list_incidents(bbox, limit)
