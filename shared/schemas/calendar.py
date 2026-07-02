"""Calendar schemas."""

from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class AvailabilityRequest(BaseModel):
    group_id: int
    date: date
    status: str = Field(..., pattern=r"^(free|busy|maybe|unknown)$")
    start_time: str | None = Field(None, pattern=r"^\d{2}:\d{2}$")
    end_time: str | None = Field(None, pattern=r"^\d{2}:\d{2}$")
    recurring_rule: str | None = None


class AvailabilityBatchRequest(BaseModel):
    group_id: int
    availabilities: list[AvailabilityRequest]


class AvailabilityResponse(BaseModel):
    id: int
    user_id: int
    group_id: int
    date: date
    status: str
    start_time: str | None = None
    end_time: str | None = None
    recurring_rule: str | None = None

    model_config = {"from_attributes": True}


class RecurringRuleRequest(BaseModel):
    group_id: int
    day_of_week: str = Field(..., pattern=r"^(monday|tuesday|wednesday|thursday|friday|saturday|sunday)$")
    status: str = Field(..., pattern=r"^(free|busy|maybe)$")
    start_time: str | None = Field(None, pattern=r"^\d{2}:\d{2}$")
    end_time: str | None = Field(None, pattern=r"^\d{2}:\d{2}$")
    date_start: date | None = None
    date_end: date | None = None


class RecurringRuleUpdateRequest(BaseModel):
    day_of_week: str | None = Field(None, pattern=r"^(monday|tuesday|wednesday|thursday|friday|saturday|sunday)$")
    status: str | None = Field(None, pattern=r"^(free|busy|maybe)$")
    start_time: str | None = Field(None, pattern=r"^\d{2}:\d{2}$")
    end_time: str | None = Field(None, pattern=r"^\d{2}:\d{2}$")
    date_start: date | None = None
    date_end: date | None = None


class RecurringRuleResponse(BaseModel):
    id: int
    user_id: int
    group_id: int
    day_of_week: str
    status: str
    start_time: str | None = None
    end_time: str | None = None
    date_start: date
    date_end: date | None = None

    model_config = {"from_attributes": True}


class GroupCalendarResponse(BaseModel):
    user_id: int
    user_name: str
    availabilities: list[AvailabilityResponse]
