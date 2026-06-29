"""User schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class UserResponse(BaseModel):
    id: int
    name: str
    email: str | None = None
    telegram_id: str | None = None
    username: str | None = None
    avatar: str | None = None
    timezone: str = "UTC"
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserUpdateRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    avatar: str | None = None
    timezone: str | None = None


class UserSettingsRequest(BaseModel):
    settings: dict = Field(default_factory=dict)
