"""Notification model."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime,  Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.database import Base

if TYPE_CHECKING:
    from shared.models.user import User


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    group_id: Mapped[Optional[int]] = mapped_column(ForeignKey("groups.id"), nullable=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g. "meeting_invite", "vote_started", "reminder"
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON payload
    is_read: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    user: Mapped["User"] = relationship(back_populates="notifications", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Notification id={self.id} user={self.user_id} type={self.type}>"
