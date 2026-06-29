"""Idea, IdeaReaction, and IdeaComment models."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime,  DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.database import Base

if TYPE_CHECKING:
    from shared.models.user import User
    from shared.models.group import Group


class ReactionType(StrEnum):
    LIKE = "👍"
    LOVE = "❤️"
    FIRE = "🔥"
    DISLIKE = "👎"


class Idea(Base):
    __tablename__ = "ideas"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cost: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # "low", "medium", "high" or "$"
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    photo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    links: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array of links
    tags: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)  # comma-separated
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    suggestor_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    is_archived: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    group: Mapped["Group"] = relationship(back_populates="ideas", lazy="selectin")
    suggestor: Mapped["User"] = relationship(back_populates="ideas", lazy="selectin")
    reactions: Mapped[list["IdeaReaction"]] = relationship(back_populates="idea", lazy="selectin", cascade="all, delete-orphan")
    comments: Mapped[list["IdeaComment"]] = relationship(back_populates="idea", lazy="selectin", cascade="all, delete-orphan")
    meetings: Mapped[list["Meeting"]] = relationship(back_populates="idea", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Idea id={self.id} title={self.title}>"


class IdeaReaction(Base):
    __tablename__ = "idea_reactions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    idea_id: Mapped[int] = mapped_column(ForeignKey("ideas.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    reaction: Mapped[ReactionType] = mapped_column(String(10), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    idea: Mapped["Idea"] = relationship(back_populates="reactions", lazy="selectin")
    user: Mapped["User"] = relationship(back_populates="reactions", lazy="selectin")

    def __repr__(self) -> str:
        return f"<IdeaReaction idea={self.idea_id} user={self.user_id} reaction={self.reaction}>"


class IdeaComment(Base):
    __tablename__ = "idea_comments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    idea_id: Mapped[int] = mapped_column(ForeignKey("ideas.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    idea: Mapped["Idea"] = relationship(back_populates="comments", lazy="selectin")

    def __repr__(self) -> str:
        return f"<IdeaComment id={self.id} idea={self.idea_id}>"
