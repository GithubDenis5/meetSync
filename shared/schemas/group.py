"""Group schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class GroupCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    min_people_for_meeting: int = Field(default=2, ge=1)


class GroupUpdateRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    min_people_for_meeting: int | None = Field(None, ge=1)


class GroupResponse(BaseModel):
    id: int
    name: str
    description: str | None = None
    invite_code: str
    owner_id: int
    min_people_for_meeting: int = 2
    created_at: datetime

    model_config = {"from_attributes": True}


class MemberAvailabilityStats(BaseModel):
    user_id: int
    user_name: str
    marked_days: int
    free_days: int


class GroupDashboardResponse(BaseModel):
    total_members: int
    total_meetings: int
    average_attendance: float
    upcoming_meetings: int
    top_ideas: list[dict]
    availability_pct: float
    member_availability: list[MemberAvailabilityStats]


class MemberResponse(BaseModel):
    id: int
    user_id: int
    name: str
    username: str | None = None
    telegram_id: str | None = None
    avatar: str | None = None
    role: str

    model_config = {"from_attributes": True}


class JoinGroupRequest(BaseModel):
    invite_code: str


class MemberRoleUpdateRequest(BaseModel):
    role: str = Field(..., pattern=r"^(ADMIN|MEMBER)$")
