"""GET /api/zones — real municipality-level danger zones. WS /ws/zones — live score pushes."""
import asyncio
import math
import random

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app import crime_stats
from app.schemas import ZoneOut

router = APIRouter(tags=["zones"])


def _label_for_score(score: float) -> str:
    # README > Home/Map Page: "no color" is the *default* — only areas with
    # an actual signal should be flagged. score is 5.5 - z*1.5 (see
    # crime_stats._score_from_rates), so these cutoffs correspond to
    # roughly +1.25 / +0.75 standard deviations above the national average
    # violent-crime rate — genuine statistical standouts, not "below
    # median this week". With a near-normal distribution that's maybe the
    # top ~10-15% of municipalities, not a third of the map.
    if score < 3.6:
        return "unsafe"
    if score < 4.4:
        return "mixed"
    return "safe"


def _geometry_bbox(geometry: dict) -> tuple[float, float, float, float]:
    lons, lats = [], []

    def walk(coords):
        if isinstance(coords[0], (int, float)):
            lons.append(coords[0])
            lats.append(coords[1])
        else:
            for c in coords:
                walk(c)

    walk(geometry["coordinates"])
    return min(lons), min(lats), max(lons), max(lats)


def _intersects(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> bool:
    a_min_lon, a_min_lat, a_max_lon, a_max_lat = a
    b_min_lon, b_min_lat, b_max_lon, b_max_lat = b
    return a_min_lon <= b_max_lon and a_max_lon >= b_min_lon and a_min_lat <= b_max_lat and a_max_lat >= b_min_lat


def _blob_polygon(center_lat: float, center_lon: float, radius_deg: float, points: int = 10) -> dict:
    """Fallback mock shape, used only while the real dataset is still loading/unreachable."""
    coords = []
    for i in range(points):
        angle = 2 * math.pi * i / points
        wobble = 0.75 + 0.25 * random.random()
        coords.append(
            [
                center_lon + radius_deg * math.cos(angle) * wobble,
                center_lat + radius_deg * math.sin(angle) * wobble * 0.7,
            ]
        )
    coords.append(coords[0])
    return {"type": "Polygon", "coordinates": [coords]}


def _fallback_zones(bbox: str) -> list[ZoneOut]:
    min_lon, min_lat, max_lon, max_lat = (float(v) for v in bbox.split(","))
    mid_lon, mid_lat = (min_lon + max_lon) / 2, (min_lat + max_lat) / 2
    span = max(max_lon - min_lon, max_lat - min_lat)
    return [
        ZoneOut(
            id="fallback-1",
            safety_score=2.8,
            safety_label=_label_for_score(2.8),
            geometry=_blob_polygon(mid_lat + span * 0.18, mid_lon - span * 0.15, span * 0.12),
        ),
    ]


@router.get("/api/zones", response_model=list[ZoneOut])
def get_zones(bbox: str = Query(..., description="minLon,minLat,maxLon,maxLat")):
    """
    Real Danish municipality polygons, colored by actual violent-crime rate
    per capita (Statistics Denmark — see app/crime_stats.py), filtered to
    whichever municipalities overlap the requested viewport.

    Falls back to a single placeholder shape if the stats cache hasn't
    populated yet (fetched once at startup + refreshed periodically — see
    main.py's lifespan) or the upstream sources were unreachable.
    """
    query_bbox = tuple(float(v) for v in bbox.split(","))
    stats = crime_stats.get_cached_stats()
    if not stats:
        return _fallback_zones(bbox)

    zones = []
    for entry in stats:
        if not _intersects(_geometry_bbox(entry.geometry), query_bbox):
            continue
        zones.append(
            ZoneOut(
                id=entry.name,
                safety_score=entry.safety_score,
                safety_label=_label_for_score(entry.safety_score),
                geometry=entry.geometry,
            )
        )
    return zones


@router.get("/api/zones/status")
def zones_status():
    """Diagnostics: is the real municipality dataset loaded, and how big is it."""
    stats = crime_stats.get_cached_stats()
    return {"municipalities_cached": len(stats)}


@router.websocket("/ws/zones")
async def zones_feed(websocket: WebSocket):
    """
    NOTE: stub. In production, this subscribes to a Redis pub/sub channel
    that Celery tasks publish to whenever a segment's score changes
    (e.g. a time-of-day bucket shift, or enough confirmed reports come in).
    Here we just emit a synthetic update every few seconds for local dev.
    """
    await websocket.accept()
    try:
        while True:
            await asyncio.sleep(5)
            await websocket.send_json(
                {
                    "segment_id": f"way-{random.randint(1000, 9999)}",
                    "safety_score": round(random.uniform(1, 10), 1),
                    "time_bucket": random.choice(["day", "evening", "night"]),
                }
            )
    except WebSocketDisconnect:
        pass
