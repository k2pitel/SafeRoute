"""Accounts: password hashing, signed session tokens, signup and login.

Reports need a login gate so they can't be spammed anonymously (F2), but
this is a single-developer prototype with no mail server or OAuth app
registered — so this deliberately skips bcrypt/PyJWT in favor of stdlib
PBKDF2 (hashlib) for password hashing and a small HMAC-signed, expiring
token for sessions. Same "avoid infrastructure this dev setup doesn't have"
reasoning as datalag/news_archive.py choosing SQLite over Postgres.

HTTP concerns (reading the Authorization header, 401s) live in
api/dependencies.py; this module knows nothing about requests.
"""
import base64
import hashlib
import hmac
import json
import secrets
import time

from app.config import settings
from app.datalag import local_store

_PBKDF2_ITERATIONS = 200_000
_TOKEN_TTL_SECONDS = 30 * 24 * 60 * 60  # 30 days — no refresh flow, so keep sessions long-lived


class EmailAlreadyRegisteredError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


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
    """The token's user id, or None if it is malformed, tampered with or expired."""
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


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def register(email: str, password: str) -> tuple[dict, str]:
    """Create an account and log it in. Returns (user, token)."""
    email = _normalize_email(email)
    if local_store.get_user_by_email(email):
        raise EmailAlreadyRegisteredError(email)
    user = local_store.create_user(email, hash_password(password))
    return user, create_token(user["id"])


def authenticate(email: str, password: str) -> tuple[dict, str]:
    """Check credentials. Returns (user, token)."""
    user = local_store.get_user_by_email(_normalize_email(email))
    if not user or not verify_password(password, user["password_hash"]):
        raise InvalidCredentialsError()
    return user, create_token(user["id"])
