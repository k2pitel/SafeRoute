"""GET /api/zones — colour-coded municipality zones (F7). WS /ws/zones — live zone updates (F5)."""
from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect

from app.api.dependencies import bbox_query
from app.api.zones import service as zones
from app.api.zones import updates as zone_updates
from app.api.zones.schemas import ZoneOut
from app.datalag import zone_cache
from app.shared.geo import BBox

router = APIRouter(tags=["zones"])


@router.get("/api/zones", response_model=list[ZoneOut])
def get_zones(
    bbox: BBox = Depends(bbox_query),
    include_safe: bool = Query(False, description="Also return uncoloured 'safe' zones"),
):
    """Real Danish municipality polygons, coloured by violent-crime rate per
    capita, filtered to the requested viewport. Empty until the Async Worker
    has loaded the data (or if the source is unreachable)."""
    return zones.zones_in_bbox(bbox, include_safe)


@router.get("/api/zones/status")
def zones_status():
    """Diagnostics: is the municipality dataset loaded, and how big is it."""
    info = zone_cache.get_info()
    return {
        "municipalities_cached": zones.cached_zone_count(),
        "crime_period": info.crime_period if info else None,
        "population_period": info.population_period if info else None,
        "fetched_at": info.fetched_at if info else None,
    }


@router.websocket("/ws/zones")
async def zones_feed(websocket: WebSocket):
    """Pushes every zone/score change the Async Worker publishes
    (api/zones/updates.py) to this client until it disconnects."""
    await websocket.accept()
    try:
        async with zone_updates.subscribe() as events:
            while True:
                await websocket.send_json(await events.get())
    except WebSocketDisconnect:
        pass
