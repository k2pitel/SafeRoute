"""GET /api/incidents — fetch incidents within a map bounding box."""
from datetime import datetime, timedelta, timezone

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

    NOTE: this is a stub that returns mock data so the endpoint is runnable
    end-to-end. Swap the body for a PostGIS ST_Within query against the
    `incidents` table once the DB is seeded, e.g.:

        SELECT * FROM incidents
        WHERE ST_Within(location::geometry, ST_MakeEnvelope(:minLon, :minLat, :maxLon, :maxLat, 4326))
        ORDER BY occurred_at DESC LIMIT :limit
    """
    min_lon, min_lat, max_lon, max_lat = (float(v) for v in bbox.split(","))
    mid_lon = (min_lon + max_lon) / 2
    mid_lat = (min_lat + max_lat) / 2

    now = datetime.now(timezone.utc)
    mock = [
        IncidentOut(
            id=1,
            type="theft",
            description="Reported bag snatching",
            latitude=mid_lat + 0.001,
            longitude=mid_lon + 0.001,
            occurred_at=now - timedelta(days=2),
            source="official",
            verified=True,
        ),
        IncidentOut(
            id=2,
            type="assault",
            description="Altercation reported near transit stop",
            latitude=mid_lat - 0.001,
            longitude=mid_lon - 0.002,
            occurred_at=now - timedelta(hours=10),
            source="community",
            verified=False,
        ),
    ]
    return mock[:limit]
