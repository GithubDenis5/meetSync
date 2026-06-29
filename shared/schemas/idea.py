"""Idea schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class IdeaCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    cost: str | None = None
    category: str | None = None
    photo_url: str | None = None
    links: str | None = None  # JSON
    tags: str | None = None
    location: str | None = None


class IdeaUpdateRequest(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    cost: str | None = None
    category: str | None = None
    photo_url: str | None = None
    links: str | None = None
    tags: str | None = None
    location: str | None = None


class IdeaResponse(BaseModel):
    id: int
    group_id: int
    title: str
    description: str | None = None
    cost: str | None = None
    category: str | None = None
    photo_url: str | None = None
    links: str | None = None
    tags: str | None = None
    location: str | None = None
    suggestor_id: int
    suggestor_name: str | None = None
    is_archived: bool = False
    reactions: dict[str, int] = {}  # reaction -> count
    created_at: datetime

    model_config = {"from_attributes": True}


class ReactionRequest(BaseModel):
    reaction: str = Field(..., pattern=r"^(👍|❤️|🔥|👎)$")


class CommentRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=1000)


class CommentResponse(BaseModel):
    id: int
    idea_id: int
    user_id: int
    user_name: str | None = None
    text: str
    created_at: datetime

    model_config = {"from_attributes": True}
