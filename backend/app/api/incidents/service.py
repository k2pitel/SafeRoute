"""Incidents (official / community / news crime points) for the map.

No real incident source is wired up yet — municipal crime portals need a
per-city ingestion adapter that doesn't exist — so this returns nothing
rather than placeholder data on the map. Once the PostGIS target schema is
live (datalag/models.py), this becomes an indexed query, e.g.:

    SELECT * FROM incidents
    WHERE ST_Within(location::geometry, ST_MakeEnvelope(:minLon, :minLat, :maxLon, :maxLat, 4326))
    ORDER BY occurred_at DESC LIMIT :limit
"""
from app.api.incidents.schemas import IncidentOut
from app.shared.geo import BBox


def list_incidents(bbox: BBox, limit: int) -> list[IncidentOut]:
    return []
