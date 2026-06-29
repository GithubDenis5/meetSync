"""User model."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime,  String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.database import Base

if TYPE_CHECKING:
    from shared.models.group import Membership
    from shared.models.calendar import Availability
    from shared.models.idea import Idea, IdeaReaction
    from shared.models.meeting import MeetingParticipant
    from shared.models.notification import Notification


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True)
    telegram_id: Mapped[Optional[str]] = mapped_column(String(100), unique=True, nullable=True)
    username: Mapped[Optional[str]] = mapped_column(String(100), unique=True, nullable=True)
    avatar: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    hashed_password: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    settings: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON
    timezone: Mapped[str] = mapped_column(String(50), default="UTC")
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    memberships: Mapped[list["Membership"]] = relationship(back_populates="user", lazy="selectin")
    availabilities: Mapped[list["Availability"]] = relationship(back_populates="user", lazy="selectin")
    ideas: Mapped[list["Idea"]] = relationship(back_populates="suggestor", lazy="selectin")
    reactions: Mapped[list["IdeaReaction"]] = relationship(back_populates="user", lazy="selectin")
    meeting_participations: Mapped[list["MeetingParticipant"]] = relationship(back_populates="user", lazy="selectin")
    notifications: Mapped[list["Notification"]] = relationship(back_populates="user", lazy="selectin")

    def __repr__(self) -> str:
        return f"<User id={self.id} name={self.name}>"
