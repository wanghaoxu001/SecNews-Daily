"""add tagging tasks

Revision ID: 008
Revises: 007
Create Date: 2026-03-29 14:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tagging_tasks",
        sa.Column("original_file_name", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("total_count", sa.Integer(), nullable=False),
        sa.Column("current_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("imported_at", sa.String(length=40), nullable=True),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_tagging_tasks_status"), "tagging_tasks", ["status"], unique=False)

    op.create_table(
        "tagging_task_items",
        sa.Column("task_id", sa.Integer(), nullable=False),
        sa.Column("row_index", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("is_important", sa.Boolean(), nullable=True),
        sa.Column("raw_payload", sa.JSON(), nullable=True),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["task_id"], ["tagging_tasks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("task_id", "row_index", name="uq_tagging_task_items_task_row"),
    )
    op.create_index(op.f("ix_tagging_task_items_task_id"), "tagging_task_items", ["task_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_tagging_task_items_task_id"), table_name="tagging_task_items")
    op.drop_table("tagging_task_items")
    op.drop_index(op.f("ix_tagging_tasks_status"), table_name="tagging_tasks")
    op.drop_table("tagging_tasks")
