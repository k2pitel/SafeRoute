"""/api/auth — local accounts (F2), plus the user's own data (US-38, US-59).

Exists so report submission can require a login (F2) instead of accepting
anonymous, unverifiable reports. Logic lives in api/auth/service.py.
"""
from fastapi import APIRouter, Depends, HTTPException, Response

from app.api.auth import service as auth
from app.api.auth.schemas import (
    LoginRequest,
    MyDataExport,
    MyReport,
    SignupRequest,
    TokenResponse,
    UserOut,
)
from app.api.dependencies import get_current_user_id

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _token_response(user: dict, token: str) -> TokenResponse:
    return TokenResponse(access_token=token, user=UserOut(id=user["id"], email=user["email"]))


@router.post("/signup", response_model=TokenResponse, status_code=201)
def signup(payload: SignupRequest):
    try:
        user, token = auth.register(payload.email, payload.password)
    except auth.EmailAlreadyRegisteredError:
        raise HTTPException(status_code=409, detail="An account with this email already exists")
    return _token_response(user, token)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest):
    try:
        user, token = auth.authenticate(payload.email, payload.password)
    except auth.TooManyLoginAttemptsError as exc:
        raise HTTPException(
            status_code=429,
            detail=f"Too many failed attempts — try again in {exc.retry_after_minutes} minutes",
            headers={"Retry-After": str(exc.retry_after_minutes * 60)},
        )
    except auth.InvalidCredentialsError:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return _token_response(user, token)


@router.get("/me/reports", response_model=list[MyReport])
def my_reports(user_id: str = Depends(get_current_user_id)):
    """US-38: the caller's own reports, newest first, with verification status."""
    return auth.my_reports(user_id)


@router.get("/me/export", response_model=MyDataExport)
def export_my_data(user_id: str = Depends(get_current_user_id)):
    """US-59 (GDPR art. 15/20): everything stored about the caller, as JSON."""
    data = auth.export_my_data(user_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Account not found")
    return data


@router.delete("/me", status_code=204)
def delete_my_account(user_id: str = Depends(get_current_user_id)):
    """US-59 (GDPR art. 17): delete the account, its reports and confirmations."""
    auth.delete_account(user_id)
    return Response(status_code=204)
