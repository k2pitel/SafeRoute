"""GET /api/incidents — fetch incidents within a map bounding box."""
from fastapi import APIRouter, Query

from app.schemas import IncidentOut

router = APIRouter(prefix="/api/incidents", tags=["incidents"])


@router.get("", response_model=list[IncidentOut])
def list_incidents(
    bbox: str = Query(..., description="minLon,minLat,maxLon,maxLat"),
    limit: int = Query(100, le=500),
):
    """
    Returns incidents inside the given bounding box.

    No real incident source is wired up yet (see README > Data Sources —
    municipal crime portals need a per-city ingestion adapter that doesn't
    exist yet), so this returns nothing rather than placeholder data. Swap
    the body for a PostGIS ST_Within query against the `incidents` table
    once that's built, e.g.:

        SELECT * FROM incidents
        WHERE ST_Within(location::geometry, ST_MakeEnvelope(:minLon, :minLat, :maxLon, :maxLat, 4326))
        ORDER BY occurred_at DESC LIMIT :limit
    """
    return []
