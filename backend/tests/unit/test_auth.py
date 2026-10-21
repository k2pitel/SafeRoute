"""Unit tests for api/auth/service.py (hashing, tokens) and the api.dependencies auth gate."""
import time

import pytest
from fastapi import HTTPException

from app.api.auth import service as auth
from app.api.dependencies import get_current_user_id


def test_password_roundtrip():
    stored = auth.hash_password("korrekt-hest")
    assert auth.verify_password("korrekt-hest", stored)
    assert not auth.verify_password("forkert", stored)


def test_same_password_gets_different_salt():
    assert auth.hash_password("abc") != auth.hash_password("abc")


def test_malformed_stored_hash_is_rejected():
    assert not auth.verify_password("abc", "no-dollar-sign")


def test_token_roundtrip():
    assert auth.decode_token(auth.create_token("user-123")) == "user-123"


def test_tampered_token_is_rejected():
    payload, signature = auth.create_token("user-123").split(".")
    assert auth.decode_token(f"{payload}.{'0' * len(signature)}") is None


def test_expired_token_is_rejected(monkeypatch):
    token = auth.create_token("user-123")
    monkeypatch.setattr(time, "time", lambda: 10**12)
    assert auth.decode_token(token) is None


@pytest.mark.parametrize("header", [None, "Token abc", "Bearer not-a-token"])
def test_dependency_rejects_missing_or_invalid_header(header):
    with pytest.raises(HTTPException) as exc:
        get_current_user_id(header)
    assert exc.value.status_code == 401
