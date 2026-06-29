"""Add status column to meeting_participants for RSVP tracking.

Revision ID: 002
Revises: 001
Create Date: 2026-06-29
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "meeting_participants",
        sa.Column("status", sa.String(20), nullable=False, server_default="maybe"),
    )


def downgrade() -> None:
    op.drop_column("meeting_participants", "status")
