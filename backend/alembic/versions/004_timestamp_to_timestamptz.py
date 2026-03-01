"""alter timestamp columns to timestamptz

Revision ID: 004
Revises: 003
Create Date: 2025-01-01 00:00:03.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# All (table, column) pairs that need migration
TIMESTAMP_COLUMNS = [
    ("rss_sources", "created_at"),
    ("rss_sources", "updated_at"),
    ("news", "published_at"),
    ("news", "created_at"),
    ("news", "updated_at"),
    ("briefings", "created_at"),
    ("briefings", "updated_at"),
    ("briefing_items", "created_at"),
    ("briefing_items", "updated_at"),
    ("llm_configs", "created_at"),
    ("llm_configs", "updated_at"),
    ("task_configs", "created_at"),
    ("task_configs", "updated_at"),
    ("importance_examples", "created_at"),
    ("importance_examples", "updated_at"),
    ("processing_configs", "created_at"),
    ("processing_configs", "updated_at"),
]


def upgrade() -> None:
    for table, column in TIMESTAMP_COLUMNS:
        op.alter_column(
            table,
            column,
            type_=sa.DateTime(timezone=True),
            existing_type=sa.DateTime(),
            existing_nullable=True,
        )


def downgrade() -> None:
    for table, column in TIMESTAMP_COLUMNS:
        op.alter_column(
            table,
            column,
            type_=sa.DateTime(),
            existing_type=sa.DateTime(timezone=True),
            existing_nullable=True,
        )
