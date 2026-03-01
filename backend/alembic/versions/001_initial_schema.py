"""initial schema

Revision ID: 001
Revises:
Create Date: 2025-01-01 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # rss_sources
    op.create_table(
        "rss_sources",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("url", sa.String(500), unique=True, nullable=False),
        sa.Column("enabled", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # news
    op.create_table(
        "news",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("url", sa.String(1000), unique=True, nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("author", sa.String(200), nullable=True),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.Column("source_id", sa.Integer(), sa.ForeignKey("rss_sources.id"), nullable=True),
        sa.Column("source_name", sa.String(200), nullable=True),
        sa.Column("title_zh", sa.String(500), nullable=True),
        sa.Column("summary_zh", sa.Text(), nullable=True),
        sa.Column("category", sa.String(50), nullable=True),
        sa.Column("process_status", sa.String(30), server_default="pending"),
        sa.Column("process_error", sa.Text(), nullable=True),
        sa.Column("embedding", Vector(1536), nullable=True),
        sa.Column("is_similar", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("similar_to_id", sa.Integer(), sa.ForeignKey("news.id"), nullable=True),
        sa.Column("similarity_details", sa.JSON(), nullable=True),
        sa.Column("is_important", sa.Boolean(), nullable=True),
        sa.Column("importance_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_news_process_status", "news", ["process_status"])
    op.create_index("ix_news_status_category", "news", ["process_status", "category"])
    op.create_index("ix_news_published_at", "news", ["published_at"])

    # briefings
    op.create_table(
        "briefings",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(20), server_default="draft"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # briefing_items
    op.create_table(
        "briefing_items",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("briefing_id", sa.Integer(), sa.ForeignKey("briefings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("news_id", sa.Integer(), sa.ForeignKey("news.id"), nullable=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("category", sa.String(50), nullable=True),
        sa.Column("sort_order", sa.Integer(), server_default="0"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # llm_configs
    op.create_table(
        "llm_configs",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("task_type", sa.String(30), unique=True, nullable=False),
        sa.Column("base_url", sa.String(500), nullable=True),
        sa.Column("api_key", sa.String(500), nullable=True),
        sa.Column("model", sa.String(100), nullable=True),
        sa.Column("temperature", sa.Float(), nullable=True),
        sa.Column("max_tokens", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # task_configs
    op.create_table(
        "task_configs",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("name", sa.String(100), unique=True, nullable=False),
        sa.Column("cron_expression", sa.String(100), nullable=False),
        sa.Column("enabled", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # importance_examples
    op.create_table(
        "importance_examples",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("is_important", sa.Boolean(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # processing_configs
    op.create_table(
        "processing_configs",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("key", sa.String(100), unique=True, nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("processing_configs")
    op.drop_table("importance_examples")
    op.drop_table("task_configs")
    op.drop_table("llm_configs")
    op.drop_table("briefing_items")
    op.drop_table("briefings")
    op.drop_table("news")
    op.drop_table("rss_sources")
    op.execute("DROP EXTENSION IF EXISTS vector")
