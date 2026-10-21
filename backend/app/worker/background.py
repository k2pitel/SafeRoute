"""Launch-variant Async Worker: asyncio tasks inside the Backend API process.

Chosen for launch (afsnit 4.3.4.5): no broker to deploy, and it handles both
periodic and event-triggered jobs at NF1's load. Limits it accepts: one
process only, and an interrupted job is not retried until its next run.
"""
import asyncio
import logging
from collections.abc import Awaitable, Callable

from app.shared.geo import BBox
from app.worker import jobs
from app.worker.base import (
    CRIME_STATS_REFRESH_INTERVAL_SECONDS,
    NEWS_POLL_INTERVAL_SECONDS,
    SEGMENT_SCORE_INTERVAL_SECONDS,
    AsyncWorker,
)

logger = logging.getLogger("saferoute.worker")

PERIODIC_JOBS: list[tuple[str, float, Callable[[], Awaitable[object]]]] = [
    ("poll_news", NEWS_POLL_INTERVAL_SECONDS, jobs.poll_news),
    ("refresh_crime_stats", CRIME_STATS_REFRESH_INTERVAL_SECONDS, jobs.refresh_crime_stats),
    ("recalculate_segment_scores", SEGMENT_SCORE_INTERVAL_SECONDS, jobs.recalculate_segment_scores),
]


class BackgroundAsyncWorker(AsyncWorker):
    def __init__(self, periodic_jobs=PERIODIC_JOBS):
        self._periodic_jobs = periodic_jobs
        self._tasks: list[asyncio.Task] = []
        self._loop: asyncio.AbstractEventLoop | None = None
        self._queue: asyncio.Queue[BBox] | None = None
        self._pending: list[BBox] = []  # submitted before start()

    async def start(self) -> None:
        self._loop = asyncio.get_running_loop()
        self._queue = asyncio.Queue()
        for area in self._pending:
            self._queue.put_nowait(area)
        self._pending.clear()

        self._tasks = [
            asyncio.create_task(self._run_periodically(name, interval, job), name=f"worker:{name}")
            for name, interval, job in self._periodic_jobs
        ]
        self._tasks.append(asyncio.create_task(self._consume_recalculations(), name="worker:recalculations"))

    async def stop(self) -> None:
        for task in self._tasks:
            task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks = []
        self._loop = None

    def submit_recalculation(self, area: BBox) -> None:
        if self._loop is None or self._queue is None:
            self._pending.append(area)
            return
        # Sync routers run in a threadpool; asyncio.Queue is not thread-safe,
        # so hand the item over to the worker's own event loop.
        self._loop.call_soon_threadsafe(self._queue.put_nowait, area)

    async def _run_periodically(self, name: str, interval: float, job: Callable[[], Awaitable[object]]) -> None:
        while True:
            try:
                await job()
            except Exception:
                logger.exception("%s failed, will retry next interval", name)
            await asyncio.sleep(interval)

    async def _consume_recalculations(self) -> None:
        assert self._queue is not None
        while True:
            area = await self._queue.get()
            try:
                await jobs.recalculate_segment_scores(area)
            except Exception:
                logger.exception("event-triggered recalculation for %s failed", area)
            finally:
                self._queue.task_done()
