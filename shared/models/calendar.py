"""Calendar and Availability models."""

from __future__ import annotations

from datetime import date, datetime, timezone
from enum import StrEnum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime,  Date, DateTime, ForeignKey, String, Text, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.database import Base

if TYPE_CHECKING:
    from shared.models.user import User
    from shared.models.group import Group


class AvailabilityStatus(StrEnum):
    FREE = "free"
    BUSY = "busy"
    MAYBE = "maybe"
    UNKNOWN = "unknown"


class Calendar(Base):
    """Group calendar configuration."""
    __tablename__ = "calendars"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), nullable=False)
    google_calendar_id: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    group: Mapped["Group"] = relationship(back_populates="calendars", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Calendar id={self.id} group={self.group_id}>"


class Availability(Base):
    __tablename__ = "availabilities"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[AvailabilityStatus] = mapped_column(String(20), default=AvailabilityStatus.UNKNOWN)
    start_time: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)  # "19:00"
    end_time: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)    # "22:00"
    recurring_rule: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # e.g. "every monday"
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="availabilities", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Availability user={self.user_id} date={self.date} status={self.status}>"


class RecurringRule(Base):
    """Recurring availability rule — "free every Monday 9-18"."""
    __tablename__ = "recurring_rules"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), nullable=False)
    day_of_week: Mapped[str] = mapped_column(String(10), nullable=False)  # monday, tuesday, ...
    status: Mapped[str] = mapped_column(String(10), default=AvailabilityStatus.FREE)
    start_time: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)  # "09:00"
    end_time: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)    # "18:00"
    date_start: Mapped[date] = mapped_column(Date, nullable=False, default=lambda: date.today())
    date_end: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="recurring_rules", lazy="selectin")

    def __repr__(self) -> str:
        return f"<RecurringRule user={self.user_id} day={self.day_of_week} status={self.status}>"
