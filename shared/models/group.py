"""Group and Membership models."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime,  DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.database import Base

if TYPE_CHECKING:
    from shared.models.user import User
    from shared.models.idea import Idea
    from shared.models.vote import Vote
    from shared.models.meeting import Meeting
    from shared.models.calendar import Calendar


class GroupRole(StrEnum):
    OWNER = "OWNER"
    ADMIN = "ADMIN"
    MEMBER = "MEMBER"


class Group(Base):
    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    invite_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    min_people_for_meeting: Mapped[int] = mapped_column(default=2)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    memberships: Mapped[list["Membership"]] = relationship(back_populates="group", lazy="selectin", cascade="all, delete-orphan")
    ideas: Mapped[list["Idea"]] = relationship(back_populates="group", lazy="selectin")
    votes: Mapped[list["Vote"]] = relationship(back_populates="group", lazy="selectin")
    meetings: Mapped[list["Meeting"]] = relationship(back_populates="group", lazy="selectin")
    calendars: Mapped[list["Calendar"]] = relationship(back_populates="group", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Group id={self.id} name={self.name}>"


class Membership(Base):
    __tablename__ = "memberships"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), nullable=False)
    role: Mapped[GroupRole] = mapped_column(String(20), default=GroupRole.MEMBER)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    user: Mapped["User"] = relationship(back_populates="memberships", lazy="selectin")
    group: Mapped["Group"] = relationship(back_populates="memberships", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Membership user={self.user_id} group={self.group_id} role={self.role}>"
