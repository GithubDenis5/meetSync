"""Vote schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class VoteCreateRequest(BaseModel):
    group_id: int
    title: str = Field(..., min_length=1, max_length=255)
    vote_type: str = Field(default="random", pattern=r"^(random|popular|category)$")
    category: Optional[str] = None
    idea_ids: list[int] = Field(default_factory=list)
    duration_hours: int = Field(default=24, ge=1, le=168)


class VoteResponseRequest(BaseModel):
    option_id: int


class VoteOptionResponse(BaseModel):
    id: int
    idea_id: int
    idea_title: str
    votes_count: int = 0

    model_config = {"from_attributes": True}


class VoteResponse(BaseModel):
    id: int
    group_id: int
    title: str
    vote_type: str
    status: str
    category: Optional[str] = None
    options: list[VoteOptionResponse] = []
    ends_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


class VoteResultResponse(BaseModel):
    vote_id: int
    title: str
    winner: Optional[VoteOptionResponse] = None
    total_votes: int = 0
    finished_at: Optional[datetime] = None
