"""GET/POST /api/reports and POST /api/reports/{id}/confirm — community reporting.

Submitting requires login (see routers/auth.py) so reports can't be spammed
anonymously — but who submitted a report is never exposed back to other
users in ReportOut, same privacy-first spirit as the differential-privacy
noise in app/privacy/laplace.py.
"""
from fastapi import APIRouter, Depends, HTTPException, Query

from app.schemas import ReportCreate, ReportOut
from app.services import local_store
from app.services.auth import get_current_user_id

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("", response_model=list[ReportOut])
def list_reports(bbox: str = Query(..., description="minLon,minLat,maxLon,maxLat")):
    min_lon, min_lat, max_lon, max_lat = (float(part) for part in bbox.split(","))
    return local_store.list_reports(min_lon, min_lat, max_lon, max_lat)


@router.post("", response_model=ReportOut, status_code=201)
def create_report(payload: ReportCreate, user_id: str = Depends(get_current_user_id)):
    """
    Submit a real-time community report (e.g. harassment, theft). Reports
    start with 0 confirmations and are weighted low in the safety score
    until nearby users confirm them (see /confirm) — see README > Machine
    Learning Approach > Community verification.
    """
    return local_store.create_report(user_id, payload)


@router.post("/{report_id}/confirm", response_model=ReportOut)
def confirm_report(report_id: int, user_id: str = Depends(get_current_user_id)):
    if not local_store.get_report(report_id):
        raise HTTPException(status_code=404, detail="Report not found")
    return local_store.confirm_report(report_id)
