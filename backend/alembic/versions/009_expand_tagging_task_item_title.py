"""expand tagging task item title

Revision ID: 009
Revises: 008
Create Date: 2026-03-29 15:10:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "009"
down_revision: Union[str, None] = "008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "tagging_task_items",
        "title",
        existing_type=sa.String(length=500),
        type_=sa.Text(),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "tagging_task_items",
        "title",
        existing_type=sa.Text(),
        type_=sa.String(length=500),
        existing_nullable=False,
    )
