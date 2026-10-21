"""Zone update broker — publish/subscribe between Async Worker and /ws/zones.

Observer pattern: the Async Worker publishes an event whenever it has
rewritten zone/score data; every open /ws/zones connection is a subscriber
and forwards the event to its Mobile Client (F5, afsnit 4.3.2). Neither
side knows about the other, only about this broker.

This in-process implementation is correct for the launch variant, where
worker and API share one process and event loop. With several Backend API
instances or the Celery worker (afsnit 4.3.4.5) the same publish/subscribe
interface is backed by Redis pub/sub instead.
"""
import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

logger = logging.getLogger("saferoute.zone_updates")

# A subscriber that stops reading (stalled socket) must not grow memory
# without bound or block the publisher; beyond this its oldest events drop.
_MAX_QUEUED_EVENTS = 100

_subscribers: set[asyncio.Queue] = set()


def publish(event: dict) -> None:
    """Fan ``event`` out to every current subscriber. Never blocks."""
    for queue in list(_subscribers):
        if queue.full():
            queue.get_nowait()  # drop the oldest rather than block the worker
        queue.put_nowait(event)
    logger.debug("zone_updates: published %s to %d subscriber(s)", event.get("type"), len(_subscribers))


@asynccontextmanager
async def subscribe() -> AsyncIterator[asyncio.Queue]:
    """``async with subscribe() as events: event = await events.get()``"""
    queue: asyncio.Queue = asyncio.Queue(maxsize=_MAX_QUEUED_EVENTS)
    _subscribers.add(queue)
    try:
        yield queue
    finally:
        _subscribers.discard(queue)


def subscriber_count() -> int:
    return len(_subscribers)
