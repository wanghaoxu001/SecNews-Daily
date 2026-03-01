"""seed default data

Revision ID: 002
Revises: 001
Create Date: 2025-01-01 00:00:01.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Default LLM config
    op.execute("""
        INSERT INTO llm_configs (task_type, base_url, api_key, model, temperature, max_tokens)
        VALUES ('default', 'http://localhost:11434', 'sk-placeholder', 'gpt-4o-mini', 0.3, 4096)
        ON CONFLICT (task_type) DO NOTHING
    """)

    # Task configs
    tasks = [
        ("fetch_rss", "0 */2 * * *", "每2小时抓取RSS"),
        ("process_news", "10 */2 * * *", "每2小时处理新闻(偏移10分钟)"),
        ("check_similarity", "20 */2 * * *", "每2小时检查相似性(偏移20分钟)"),
        ("judge_importance", "30 */2 * * *", "每2小时判断重要性(偏移30分钟)"),
        ("full_pipeline", "0 6 * * *", "每天早上6点完整流水线"),
    ]
    for name, cron, desc in tasks:
        op.execute(f"""
            INSERT INTO task_configs (name, cron_expression, enabled, description)
            VALUES ('{name}', '{cron}', true, '{desc}')
            ON CONFLICT (name) DO NOTHING
        """)

    # Default processing configs
    configs = [
        ("similarity_threshold", "0.5", "相似性判定阈值"),
        ("similarity_days", "7", "相似性比较的天数范围"),
        ("similarity_top_k", "3", "送LLM判定的候选数量"),
        ("embedding_dim", "1536", "向量维度"),
        ("entity_weight", "0.3", "实体匹配权重"),
        ("keyword_weight", "0.4", "关键词相似度权重"),
        ("embedding_weight", "0.3", "向量相似度权重"),
    ]
    for key, value, desc in configs:
        op.execute(f"""
            INSERT INTO processing_configs (key, value, description)
            VALUES ('{key}', '{value}', '{desc}')
            ON CONFLICT (key) DO NOTHING
        """)


def downgrade() -> None:
    op.execute("DELETE FROM processing_configs WHERE key IN ('similarity_threshold','similarity_days','similarity_top_k','embedding_dim','entity_weight','keyword_weight','embedding_weight')")
    op.execute("DELETE FROM task_configs WHERE name IN ('fetch_rss','process_news','check_similarity','judge_importance','full_pipeline')")
    op.execute("DELETE FROM llm_configs WHERE task_type = 'default'")
