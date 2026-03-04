"""add crawl diagnostics fields to news

Revision ID: 005
Revises: 004
Create Date: 2026-03-04 00:00:05.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("news", sa.Column("crawl_error_code", sa.String(length=64), nullable=True))
    op.add_column("news", sa.Column("crawl_error_detail", sa.Text(), nullable=True))
    op.add_column("news", sa.Column("crawl_attempts", sa.Integer(), nullable=True))
    op.add_column("news", sa.Column("crawl_last_duration_ms", sa.Integer(), nullable=True))
    op.add_column("news", sa.Column("crawl_last_attempt_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("news", "crawl_last_attempt_at")
    op.drop_column("news", "crawl_last_duration_ms")
    op.drop_column("news", "crawl_attempts")
    op.drop_column("news", "crawl_error_detail")
    op.drop_column("news", "crawl_error_code")
