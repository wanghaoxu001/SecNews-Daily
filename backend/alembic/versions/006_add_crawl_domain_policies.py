"""add crawl domain policies

Revision ID: 006
Revises: 005
Create Date: 2026-03-04 00:20:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "crawl_domain_policies",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("domain", sa.String(length=255), nullable=False),
        sa.Column("wait_for_chain", sa.JSON(), nullable=True),
        sa.Column("timeouts_ms", sa.JSON(), nullable=True),
        sa.Column("simulate_user", sa.Boolean(), nullable=True),
        sa.Column("magic", sa.Boolean(), nullable=True),
        sa.Column("probe_status", sa.String(length=20), nullable=False),
        sa.Column("probe_sample_size", sa.Integer(), nullable=True),
        sa.Column("probe_success_rate", sa.Float(), nullable=True),
        sa.Column("probe_avg_duration_ms", sa.Integer(), nullable=True),
        sa.Column("probe_last_error", sa.Text(), nullable=True),
        sa.Column("probe_last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("domain"),
    )
    op.create_index("ix_crawl_domain_policies_domain", "crawl_domain_policies", ["domain"], unique=False)
    op.create_index("ix_crawl_domain_policies_probe_status", "crawl_domain_policies", ["probe_status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_crawl_domain_policies_probe_status", table_name="crawl_domain_policies")
    op.drop_index("ix_crawl_domain_policies_domain", table_name="crawl_domain_policies")
    op.drop_table("crawl_domain_policies")
