"""WS /ws/zones — live push of zone/safety-score changes."""
import asyncio
import random

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter(tags=["zones"])


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
