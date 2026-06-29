"""Update meetings table from old (idea-based) to new (RSVP/event) schema.

Revision ID: 003
Revises: 002
Create Date: 2026-06-29
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new columns to meetings
    op.add_column("meetings", sa.Column("title", sa.String(255), nullable=True))
    op.add_column("meetings", sa.Column("description", sa.Text(), nullable=True))
    op.add_column("meetings", sa.Column("time", sa.String(10), nullable=True))
    op.add_column("meetings", sa.Column("creator_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True))

    # Drop old columns (keep idea_id — it links meetings to proposed ideas)
    op.drop_column("meetings", "comment")


def downgrade() -> None:
    # Add old columns back
    op.add_column("meetings", sa.Column("comment", sa.Text(), nullable=True))

    # Drop new columns
    op.drop_column("meetings", "title")
    op.drop_column("meetings", "description")
    op.drop_column("meetings", "time")
    op.drop_column("meetings", "creator_id")
