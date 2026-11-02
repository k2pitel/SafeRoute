"""POST /api/auth/signup and /api/auth/login, GET/DELETE /api/auth/me (US-59)."""
import re
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

# Pragmatic shape check (US-58): something@something.tld, no spaces. Real
# deliverability would need a confirmation mail, which this setup doesn't send.
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$")

MIN_PASSWORD_LENGTH = 8


class SignupRequest(BaseModel):
    email: str = Field(..., max_length=254)
    password: str = Field(..., min_length=MIN_PASSWORD_LENGTH, max_length=256)

    @field_validator("email")
    @classmethod
    def email_shape(cls, value: str) -> str:
        value = value.strip()
        if not _EMAIL_RE.match(value):
            raise ValueError("Enter a valid email address")
        return value


class LoginRequest(BaseModel):
    email: str = Field(..., max_length=254)
    password: str = Field(..., max_length=256)


class UserOut(BaseModel):
    id: str
    email: str


class TokenResponse(BaseModel):
    access_token: str
    user: UserOut


class MyReport(BaseModel):
    """One of the caller's own reports (US-38): includes verification status,
    never anything about who confirmed it."""

    id: int
    type: str
    latitude: float
    longitude: float
    description: str | None = None
    occurred_at: datetime
    created_at: datetime
    confirmations: int
    verified: bool


class MyDataExport(BaseModel):
    """GDPR data export (US-59, art. 15/20): everything stored about the user."""

    user: UserOut
    created_at: datetime
    reports: list[MyReport]
    confirmations_given: int
    exported_at: datetime
