"""POST /api/auth/signup and /api/auth/login — local accounts.

Exists so report submission (routers/reports.py) can require a login
instead of accepting anonymous, unverifiable reports — see
app/services/auth.py for why this is email+password with no external
mail/OAuth dependency.
"""
from fastapi import APIRouter, HTTPException

from app.schemas import LoginRequest, SignupRequest, TokenResponse, UserOut
from app.services import auth, local_store

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/signup", response_model=TokenResponse, status_code=201)
def signup(payload: SignupRequest):
    email = payload.email.strip().lower()
    if local_store.get_user_by_email(email):
        raise HTTPException(status_code=409, detail="An account with this email already exists")
    user = local_store.create_user(email, auth.hash_password(payload.password))
    token = auth.create_token(user["id"])
    return TokenResponse(access_token=token, user=UserOut(id=user["id"], email=user["email"]))


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest):
    email = payload.email.strip().lower()
    user = local_store.get_user_by_email(email)
    if not user or not auth.verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = auth.create_token(user["id"])
    return TokenResponse(access_token=token, user=UserOut(id=user["id"], email=user["email"]))
