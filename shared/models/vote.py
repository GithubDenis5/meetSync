"""Vote, VoteOption, and VoteResponse models."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime,  Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.database import Base

if TYPE_CHECKING:
    from shared.models.user import User
    from shared.models.group import Group


class VoteType(StrEnum):
    RANDOM = "random"
    POPULAR = "popular"
    CATEGORY = "category"


class VoteStatus(StrEnum):
    ACTIVE = "active"
    FINISHED = "finished"
    CANCELLED = "cancelled"


class Vote(Base):
    __tablename__ = "votes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    vote_type: Mapped[VoteType] = mapped_column(String(20), default=VoteType.RANDOM)
    status: Mapped[VoteStatus] = mapped_column(String(20), default=VoteStatus.ACTIVE)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    group: Mapped["Group"] = relationship(back_populates="votes", lazy="selectin")
    options: Mapped[list["VoteOption"]] = relationship(back_populates="vote", lazy="selectin", cascade="all, delete-orphan")
    responses: Mapped[list["VoteResponse"]] = relationship(back_populates="vote", lazy="selectin", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Vote id={self.id} group={self.group_id} status={self.status}>"


class VoteOption(Base):
    """An idea that's an option in a vote."""
    __tablename__ = "vote_options"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    vote_id: Mapped[int] = mapped_column(ForeignKey("votes.id"), nullable=False)
    idea_id: Mapped[int] = mapped_column(ForeignKey("ideas.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    vote: Mapped["Vote"] = relationship(back_populates="options", lazy="selectin")

    def __repr__(self) -> str:
        return f"<VoteOption vote={self.vote_id} idea={self.idea_id}>"


class VoteResponse(Base):
    __tablename__ = "vote_responses"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    vote_id: Mapped[int] = mapped_column(ForeignKey("votes.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    option_id: Mapped[int] = mapped_column(ForeignKey("vote_options.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    vote: Mapped["Vote"] = relationship(back_populates="responses", lazy="selectin")

    def __repr__(self) -> str:
        return f"<VoteResponse vote={self.vote_id} user={self.user_id} option={self.option_id}>"
