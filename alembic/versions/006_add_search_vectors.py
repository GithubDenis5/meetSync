"""Add tsvector search vectors to ideas and meetings tables.

Adds GENERATED ALWAYS columns with PostgreSQL full-text search vectors
and GIN indexes for fast text search.

Revision ID: 006
Revises: 005
Create Date: 2026-06-30
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add search_vector to ideas table
    op.add_column(
        "ideas",
        sa.Column(
            "search_vector",
            postgresql.TSVECTOR(),
            sa.Computed(
                "to_tsvector('english', "
                "coalesce(title, '') || ' ' || "
                "coalesce(description, '') || ' ' || "
                "coalesce(category, '') || ' ' || "
                "coalesce(tags, '') || ' ' || "
                "coalesce(location, '')"
                ")",
                persisted=True,
            ),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_ideas_search_vector",
        "ideas",
        ["search_vector"],
        postgresql_using="gin",
    )

    # Add search_vector to meetings table
    op.add_column(
        "meetings",
        sa.Column(
            "search_vector",
            postgresql.TSVECTOR(),
            sa.Computed(
                "to_tsvector('english', "
                "coalesce(title, '') || ' ' || "
                "coalesce(description, '') || ' ' || "
                "coalesce(location, '')"
                ")",
                persisted=True,
            ),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_meetings_search_vector",
        "meetings",
        ["search_vector"],
        postgresql_using="gin",
    )


def downgrade() -> None:
    op.drop_index("ix_meetings_search_vector", table_name="meetings")
    op.drop_column("meetings", "search_vector")
    op.drop_index("ix_ideas_search_vector", table_name="ideas")
    op.drop_column("ideas", "search_vector")
