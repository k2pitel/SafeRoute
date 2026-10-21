"""GET /api/zones — colour-coded municipality zones (F7). WS /ws/zones — live zone updates (F5)."""
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from app.api.dependencies import bbox_query
from app.api.zones import service as zones
from app.api.zones import updates as zone_updates
from app.api.zones.schemas import ZoneOut
from app.shared.geo import BBox

router = APIRouter(tags=["zones"])


@router.get("/api/zones", response_model=list[ZoneOut])
def get_zones(bbox: BBox = Depends(bbox_query)):
    """Real Danish municipality polygons, coloured by violent-crime rate per
    capita, filtered to the requested viewport. Empty until the Async Worker
    has loaded the data (or if the source is unreachable)."""
    return zones.zones_in_bbox(bbox)


@router.get("/api/zones/status")
def zones_status():
    """Diagnostics: is the municipality dataset loaded, and how big is it."""
    return {"municipalities_cached": zones.cached_zone_count()}


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
