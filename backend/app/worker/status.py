"""Job health for GET /api/pipeline/status (DP-07).

Each Async Worker job reports how its last run went. A job counts as
stale after two missed runs, so stale data is never shown as fresh. In
memory: correct for the launch variant (worker inside the API process);
the Celery variant would need this in Redis (US-35).
"""
import threading
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta


@dataclass
class JobStatus:
    name: str
    interval_seconds: float
    last_success: datetime | None = None
    last_error: str | None = None
    last_error_at: datetime | None = None
    last_result: object = None
    runs: int = 0
    failures: int = 0

    def stale(self, now: datetime) -> bool:
        if self.last_success is None:
            return self.runs > 0  # has run but never succeeded
        return now - self.last_success > timedelta(seconds=self.interval_seconds * 2)


_jobs: dict[str, JobStatus] = {}
_lock = threading.Lock()


def register(name: str, interval_seconds: float) -> None:
    with _lock:
        _jobs.setdefault(name, JobStatus(name, interval_seconds))


def record_success(name: str, result: object = None) -> None:
    with _lock:
        job = _jobs.setdefault(name, JobStatus(name, 0))
        job.runs += 1
        job.last_success = datetime.now(UTC)
        job.last_result = result if isinstance(result, (int, float, str, type(None))) else str(result)


def record_failure(name: str, error: BaseException) -> None:
    with _lock:
        job = _jobs.setdefault(name, JobStatus(name, 0))
        job.runs += 1
        job.failures += 1
        job.last_error = f"{type(error).__name__}: {error}"[:300]
        job.last_error_at = datetime.now(UTC)


def snapshot() -> list[dict]:
    now = datetime.now(UTC)
    with _lock:
        return [
            {
                "job": j.name,
                "interval_minutes": round(j.interval_seconds / 60, 1),
                "last_success": j.last_success,
                "last_result": j.last_result,
                "last_error": j.last_error,
                "last_error_at": j.last_error_at,
                "runs": j.runs,
                "failures": j.failures,
                "stale": j.stale(now),
            }
            for j in _jobs.values()
        ]


def reset() -> None:
    with _lock:
        _jobs.clear()

