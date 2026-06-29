"""Meeting schemas."""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class MeetingCreateRequest(BaseModel):
    group_id: int
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    date: date
    time: Optional[str] = Field(None, pattern=r"^\d{2}:\d{2}$")
    location: Optional[str] = None
    idea_id: Optional[int] = None


class MeetingUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    date: Optional[date] = None
    time: Optional[str] = None
    location: Optional[str] = None


class RsvpRequest(BaseModel):
    status: str = Field(..., pattern=r"^(going|not_going|maybe)$")


class ParticipantResponse(BaseModel):
    user_id: int
    user_name: str
    status: str

    model_config = {"from_attributes": True}


class MeetingResponse(BaseModel):
    id: int
    group_id: int
    idea_id: Optional[int] = None
    idea_title: Optional[str] = None
    title: str
    description: Optional[str] = None
    date: date
    time: Optional[str] = None
    location: Optional[str] = None
    photo_url: Optional[str] = None
    creator_id: int
    creator_name: Optional[str] = None
    participants: list[ParticipantResponse] = []
    created_at: datetime

    model_config = {"from_attributes": True}
