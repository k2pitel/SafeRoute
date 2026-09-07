"""Password hashing + signed session tokens for local accounts.

Reports need a login gate so they can't be spammed anonymously (see
routers/reports.py), but this is a single-developer prototype with no
mail server or OAuth app registered — so this deliberately skips
bcrypt/PyJWT in favor of stdlib PBKDF2 (hashlib) for password hashing and
a small HMAC-signed, expiring token for sessions. Same "avoid
infrastructure this dev setup doesn't have" reasoning as
services/news_archive.py choosing SQLite over Postgres.
"""
import base64
import hashlib
import hmac
import json
import secrets
import time

from fastapi import Header, HTTPException

from app.config import settings

_PBKDF2_ITERATIONS = 200_000
_TOKEN_TTL_SECONDS = 30 * 24 * 60 * 60  # 30 days — no refresh flow, so keep sessions long-lived


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), _PBKDF2_ITERATIONS).hex()
    return f"{salt}${digest}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt, digest = stored.split("$", 1)
    except ValueError:
        return False
    candidate = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), _PBKDF2_ITERATIONS).hex()
    return hmac.compare_digest(candidate, digest)


def create_token(user_id: str) -> str:
    payload = json.dumps({"sub": user_id, "exp": int(time.time()) + _TOKEN_TTL_SECONDS}).encode()
    payload_b64 = base64.urlsafe_b64encode(payload).decode().rstrip("=")
    signature = hmac.new(settings.jwt_secret_key.encode(), payload_b64.encode(), hashlib.sha256).hexdigest()
    return f"{payload_b64}.{signature}"


def decode_token(token: str) -> str | None:
    try:
        payload_b64, signature = token.split(".", 1)
    except ValueError:
        return None
    expected = hmac.new(settings.jwt_secret_key.encode(), payload_b64.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        return None
    try:
        padded = payload_b64 + "=" * (-len(payload_b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded))
    except (ValueError, UnicodeDecodeError):
        return None
    if payload.get("exp", 0) < time.time():
        return None
    return payload.get("sub")


def get_current_user_id(authorization: str | None = Header(default=None)) -> str:
    """FastAPI dependency — raises 401 unless a valid `Authorization: Bearer <token>` is present."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Login required to do that")
    user_id = decode_token(authorization.removeprefix("Bearer "))
    if not user_id:
        raise HTTPException(status_code=401, detail="Session expired — please log in again")
    return user_id
