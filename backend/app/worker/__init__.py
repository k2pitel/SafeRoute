"""Async Worker — the background-processing subsystem (figur 4.2, afsnit 4.3).

Keeps data fresh outside the request path: crime-news polling, zone-score
refresh and segment-score recalculation (periodic + event-triggered).

The rest of the system depends only on the ``AsyncWorker`` interface, so
its realisation can change without touching any other subsystem
(afsnit 4.3.4.5):

- ``BackgroundAsyncWorker`` (worker/background.py) — launch variant:
  asyncio tasks inside the Backend API process.
- ``CeleryAsyncWorker`` (worker/celery_worker.py) — target architecture:
  Celery worker + Beat with Redis as broker.

Both run the same job functions (worker/jobs.py).
"""
from app.worker.base import AsyncWorker

__all__ = ["AsyncWorker"]
