"""GET/POST /api/reports and POST /api/reports/{id}/confirm — community reporting (F2, F3).

Submitting and confirming require login; who submitted a report is never
exposed back to other users (ReportOut has no user_id, NF11).
"""
from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import bbox_query, get_async_worker, get_current_user_id
from app.api.reports import service as reports
from app.api.reports.schemas import ReportCreate, ReportOut
from app.shared.geo import BBox
from app.worker import AsyncWorker

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("", response_model=list[ReportOut])
def list_reports(bbox: BBox = Depends(bbox_query)):
    return reports.list_reports(bbox)


@router.post("", response_model=ReportOut, status_code=201)
def create_report(payload: ReportCreate, user_id: str = Depends(get_current_user_id)):
    """Submit a real-time community report (e.g. harassment, theft). Starts
    with 0 confirmations and is weighted low until nearby users confirm it.
    429 once the user hits the NF10 rate limit."""
    try:
        return reports.create_report(user_id, payload)
    except reports.RateLimitExceededError as exc:
        raise HTTPException(
            status_code=429,
            detail=f"Too many reports — please wait up to {exc.retry_after_minutes} minutes before reporting again",
            headers={"Retry-After": str(exc.retry_after_minutes * 60)},
        )


@router.post("/{report_id}/confirm", response_model=ReportOut)
def confirm_report(
    report_id: int,
    user_id: str = Depends(get_current_user_id),
    async_worker: AsyncWorker = Depends(get_async_worker),
):
    """F3: another user vouches for the report. Each user can confirm a report
    once (409) and never their own (403)."""
    try:
        return reports.confirm_report(report_id, user_id, async_worker)
    except reports.ReportNotFoundError:
        raise HTTPException(status_code=404, detail="Report not found")
    except reports.OwnReportError:
        raise HTTPException(status_code=403, detail="You can't confirm your own report")
    except reports.AlreadyConfirmedError:
        raise HTTPException(status_code=409, detail="You have already confirmed this report")
