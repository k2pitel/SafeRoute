"""POST /api/reports and POST /api/reports/{id}/confirm — community reporting."""
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from app.schemas import ReportCreate, ReportOut

router = APIRouter(prefix="/api/reports", tags=["reports"])

# In-memory store as a stub; replace with the `reports` DB table.
_REPORTS: dict[int, ReportOut] = {}
_NEXT_ID = 1


@router.post("", response_model=ReportOut, status_code=201)
def create_report(payload: ReportCreate):
    """
    Submit a real-time community report. Reports start with 0 confirmations
    and are weighted low in the safety score until nearby users confirm them
    (see /confirm) — see README > Machine Learning Approach > Community verification.
    """
    global _NEXT_ID
    report = ReportOut(
        id=_NEXT_ID,
        latitude=payload.latitude,
        longitude=payload.longitude,
        description=payload.description,
        confirmations=0,
        created_at=datetime.now(timezone.utc),
    )
    _REPORTS[_NEXT_ID] = report
    _NEXT_ID += 1
    return report


@router.post("/{report_id}/confirm", response_model=ReportOut)
def confirm_report(report_id: int):
    report = _REPORTS.get(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    report.confirmations += 1
    return report
