"""Notification schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class NotificationResponse(BaseModel):
    id: int
    user_id: int
    type: str
    title: str
    message: str | None = None
    data: str | None = None
    is_read: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}
