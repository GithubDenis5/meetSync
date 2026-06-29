"""Auth schemas."""

from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    email: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=6, max_length=128)


class LoginRequest(BaseModel):
    email: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class TelegramAuthRequest(BaseModel):
    telegram_id: str
    username: str | None = None


class AuthUserResponse(BaseModel):
    id: int
    name: str
    email: str | None = None
    telegram_id: str | None = None
    username: str | None = None
    avatar: str | None = None
    timezone: str = "UTC"
