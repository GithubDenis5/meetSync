"""Meeting and MeetingParticipant models."""

from __future__ import annotations

from datetime import date, datetime, timezone
from enum import StrEnum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime,  Date, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.database import Base

if TYPE_CHECKING:
    from shared.models.user import User
    from shared.models.group import Group
    from shared.models.idea import Idea


class RsvpStatus(StrEnum):
    GOING = "going"
    NOT_GOING = "not_going"
    MAYBE = "maybe"


class Meeting(Base):
    __tablename__ = "meetings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), nullable=False)
    idea_id: Mapped[Optional[int]] = mapped_column(ForeignKey("ideas.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    time: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)  # "19:00"
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    photo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    creator_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    group: Mapped["Group"] = relationship(back_populates="meetings", lazy="selectin")
    idea: Mapped[Optional["Idea"]] = relationship(back_populates="meetings", lazy="selectin")
    creator: Mapped["User"] = relationship(foreign_keys=[creator_id], lazy="selectin")
    participants: Mapped[list["MeetingParticipant"]] = relationship(
        back_populates="meeting", lazy="selectin", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Meeting id={self.id} group={self.group_id} date={self.date}>"


class MeetingParticipant(Base):
    __tablename__ = "meeting_participants"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    meeting_id: Mapped[int] = mapped_column(ForeignKey("meetings.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    status: Mapped[RsvpStatus] = mapped_column(String(20), default=RsvpStatus.MAYBE)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    meeting: Mapped["Meeting"] = relationship(back_populates="participants", lazy="selectin")
    user: Mapped["User"] = relationship(back_populates="meeting_participations", lazy="selectin")

    def __repr__(self) -> str:
        return f"<MeetingParticipant meeting={self.meeting_id} user={self.user_id} status={self.status}>"
