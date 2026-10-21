"""POST /api/auth/signup and /api/auth/login — local accounts.

Exists so report submission can require a login (F2) instead of accepting
anonymous, unverifiable reports. Logic lives in api/auth/service.py.
"""
from fastapi import APIRouter, HTTPException

from app.api.auth import service as auth
from app.api.auth.schemas import LoginRequest, SignupRequest, TokenResponse, UserOut

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
    except auth.InvalidCredentialsError:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return _token_response(user, token)
