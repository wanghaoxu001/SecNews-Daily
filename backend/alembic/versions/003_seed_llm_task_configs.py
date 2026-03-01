"""seed llm configs for all task types

Revision ID: 003
Revises: 002
Create Date: 2025-01-01 00:00:02.000000
"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TASK_TYPES = ["translate", "summarize", "classify", "similarity", "importance", "embedding"]


def upgrade() -> None:
    for tt in TASK_TYPES:
        op.execute(f"""
            INSERT INTO llm_configs (task_type)
            VALUES ('{tt}')
            ON CONFLICT (task_type) DO NOTHING
        """)


def downgrade() -> None:
    types_str = ", ".join(f"'{t}'" for t in TASK_TYPES)
    op.execute(f"DELETE FROM llm_configs WHERE task_type IN ({types_str})")
