"""Add recurring_rules table for weekly availability patterns.

Revision ID: 004
Revises: 003
Create Date: 2026-06-30
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "recurring_rules",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("group_id", sa.Integer(), sa.ForeignKey("groups.id"), nullable=False),
        sa.Column("day_of_week", sa.String(10), nullable=False),
        sa.Column("status", sa.String(10), nullable=False, server_default="free"),
        sa.Column("start_time", sa.String(5), nullable=True),
        sa.Column("end_time", sa.String(5), nullable=True),
        sa.Column("date_start", sa.Date(), nullable=False,
                  server_default=sa.text("CURRENT_DATE")),
        sa.Column("date_end", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_recurring_rules_user_group", "recurring_rules",
                    ["user_id", "group_id"])


def downgrade() -> None:
    op.drop_index("ix_recurring_rules_user_group", table_name="recurring_rules")
    op.drop_table("recurring_rules")
