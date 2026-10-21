"""Community reports — UC2 (F2), verification (F3), event-driven rescoring (NF5).

NF4 (a new report visible within 2 min) is met by reading reports straight
from the Datalag: a new report is in the next GET /api/reports.

NF5 (a verified report affects the score within 5 min) can't wait for the
Async Worker's periodic run (every 15 min), so — per afsnit 4.2.3 — the
confirmation that makes a report verified submits a targeted recalculation
job for the surrounding area instead of a full rerun for the whole city.

NF10 (anti-spam) is enforced here, not in the router, so every way of
creating a report is covered: a rolling per-user limit on submissions, and
a report only counts confirmations from *other* users, once each (F3).
"""
from datetime import UTC, datetime, timedelta

from app.api.reports.schemas import ReportCreate
from app.config import settings
from app.datalag import local_store
from app.shared.geo import BBox
from app.worker import AsyncWorker

# Area around a verified report whose segments get rescored (~500 m).
RECALCULATION_RADIUS_DEGREES = 0.005


class ReportNotFoundError(Exception):
    pass


class RateLimitExceededError(Exception):
    """The user has hit the NF10 limit; ``retry_after_minutes`` is the window size."""

    def __init__(self, retry_after_minutes: int):
        super().__init__(retry_after_minutes)
        self.retry_after_minutes = retry_after_minutes


class OwnReportError(Exception):
    """A user tried to confirm their own report."""


class AlreadyConfirmedError(Exception):
    """The user has already confirmed this report."""


def list_reports(bbox: BBox) -> list[dict]:
    return local_store.list_reports(bbox.min_lon, bbox.min_lat, bbox.max_lon, bbox.max_lat)


def create_report(user_id: str, report: ReportCreate) -> dict:
    """Stored unconfirmed (0 confirmations): weighted low until verified (F3)."""
    window = timedelta(minutes=settings.report_rate_window_minutes)
    recent = local_store.count_reports_by_user_since(user_id, datetime.now(UTC) - window)
    if recent >= settings.report_rate_limit:
        raise RateLimitExceededError(settings.report_rate_window_minutes)
    return local_store.create_report(user_id, report)


def _surrounding_area(report: dict) -> BBox:
    r = RECALCULATION_RADIUS_DEGREES
    return BBox(report["longitude"] - r, report["latitude"] - r, report["longitude"] + r, report["latitude"] + r)


def confirm_report(report_id: int, user_id: str, async_worker: AsyncWorker) -> dict:
    existing = local_store.get_report(report_id)
    if not existing:
        raise ReportNotFoundError(report_id)
    if existing["user_id"] == user_id:
        raise OwnReportError(report_id)
    if not local_store.add_confirmation(report_id, user_id):
        raise AlreadyConfirmedError(report_id)
    report = local_store.get_report(report_id)

    # Exactly at the threshold, not >=, so each report triggers one job when
    # it becomes verified rather than one per extra confirmation.
    if report["confirmations"] == settings.report_verification_threshold:
        async_worker.submit_recalculation(_surrounding_area(report))
    return report
