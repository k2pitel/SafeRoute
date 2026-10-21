"""Target-architecture Async Worker, as seen from the Backend API.

The Celery worker and Beat scheduler run as their own process, so start/stop
are no-ops here; the API's only job is to enqueue event-triggered work on
the Redis broker.
"""
from app.shared.geo import BBox
from app.worker.base import AsyncWorker


class CeleryAsyncWorker(AsyncWorker):
    async def start(self) -> None:
        pass  # periodic jobs are scheduled by Celery Beat in the worker container

    async def stop(self) -> None:
        pass

    def submit_recalculation(self, area: BBox) -> None:
        from app.worker import tasks  # imported lazily: needs Celery/Redis config only when used

        tasks.recalculate_segment_scores.delay(list(area))
