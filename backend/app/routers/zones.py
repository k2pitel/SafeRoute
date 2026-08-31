"""GET /api/zones — clustered danger zones. WS /ws/zones — live score pushes."""
import asyncio
import math
import random

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.schemas import ZoneOut

router = APIRouter(tags=["zones"])


def _label_for_score(score: float) -> str:
    if score < 4:
        return "unsafe"
    if score < 6.5:
        return "mixed"
    return "safe"


def _blob_polygon(center_lat: float, center_lon: float, radius_deg: float, points: int = 10) -> dict:
    """A rough hand-outlined-looking polygon around a center point."""
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


@router.get("/api/zones", response_model=list[ZoneOut])
def get_zones(bbox: str = Query(..., description="minLon,minLat,maxLon,maxLat")):
    """
    Returns danger-cluster polygons inside the given bounding box.

    NOTE: stub. In production this clusters adjacent low-scoring
    `segment_scores` rows (e.g. DBSCAN over segment midpoints) and returns
    the resulting cluster hulls. Here we return a couple of mock zones
    positioned relative to the requested bbox, so they show up wherever the
    map is currently looking, for local dev.
    """
    min_lon, min_lat, max_lon, max_lat = (float(v) for v in bbox.split(","))
    mid_lon = (min_lon + max_lon) / 2
    mid_lat = (min_lat + max_lat) / 2
    span = max(max_lon - min_lon, max_lat - min_lat)

    red_score = 2.8
    yellow_score = 5.2
    return [
        ZoneOut(
            id="zone-1",
            safety_score=red_score,
            safety_label=_label_for_score(red_score),
            geometry=_blob_polygon(mid_lat + span * 0.18, mid_lon - span * 0.15, span * 0.12),
        ),
        ZoneOut(
            id="zone-2",
            safety_score=yellow_score,
            safety_label=_label_for_score(yellow_score),
            geometry=_blob_polygon(mid_lat - span * 0.15, mid_lon + span * 0.2, span * 0.1),
        ),
    ]


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
