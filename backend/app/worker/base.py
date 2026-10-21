"""The Async Worker interface every realisation implements."""
from abc import ABC, abstractmethod

from app.shared.geo import BBox

# Periodic schedule (afsnit 4.2.1, 4.3.2). Shared by both realisations so
# the launch variant and the Celery Beat schedule can't drift apart.
NEWS_POLL_INTERVAL_SECONDS = 15 * 60  # nyhedskilder: every 15 minutes
CRIME_STATS_REFRESH_INTERVAL_SECONDS = 6 * 60 * 60  # offentlige data: every 6 hours (they change quarterly)
SEGMENT_SCORE_INTERVAL_SECONDS = 15 * 60  # periodic tryghedsscore recalculation


class AsyncWorker(ABC):
    """Runs periodic jobs on its own schedule and accepts event-triggered ones."""

    @abstractmethod
    async def start(self) -> None:
        """Begin running periodic jobs. Called once on Backend API startup."""

    @abstractmethod
    async def stop(self) -> None:
        """Stop all jobs. Called once on Backend API shutdown."""

    @abstractmethod
    def submit_recalculation(self, area: BBox) -> None:
        """Queue a targeted segment-score recalculation for ``area``
        (event-triggered, NF5). Must return immediately and be safe to call
        from request-handling threads."""
