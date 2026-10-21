"""POST /api/auth/signup and /api/auth/login."""
from pydantic import BaseModel, Field


class SignupRequest(BaseModel):
    email: str
    password: str = Field(..., min_length=1)


class LoginRequest(BaseModel):
    email: str
    password: str


class UserOut(BaseModel):
    id: str
    email: str


class TokenResponse(BaseModel):
    access_token: str
    user: UserOut
