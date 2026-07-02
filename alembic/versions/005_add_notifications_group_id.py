"""Add group_id to notifications table for group activity feed.

Revision ID: 005
Revises: 004
Create Date: 2026-06-30
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("notifications", sa.Column("group_id", sa.Integer(), sa.ForeignKey("groups.id"), nullable=True))
    op.create_index("ix_notifications_group", "notifications", ["group_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_notifications_group", table_name="notifications")
    op.drop_column("notifications", "group_id")
