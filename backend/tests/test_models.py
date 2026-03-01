"""Test that all models are importable and metadata is correct."""
from app.models import (
    Base, RssSource, News, Briefing, BriefingItem,
    LlmConfig, TaskConfig, ImportanceExample, ProcessingConfig,
    ProcessStatus, NewsCategory, BriefingStatus, LlmTaskType,
)


def test_all_tables_registered():
    tables = set(Base.metadata.tables.keys())
    expected = {
        "rss_sources", "news", "briefings", "briefing_items",
        "llm_configs", "task_configs", "importance_examples", "processing_configs",
    }
    assert tables == expected


def test_process_status_enum():
    assert ProcessStatus.pending.value == "pending"
    assert ProcessStatus.completed.value == "completed"
    assert ProcessStatus.failed.value == "failed"


def test_news_category_enum():
    assert NewsCategory.financial_cyber.value == "金融业网络安全事件"
    assert NewsCategory.other.value == "其他"
    assert len(NewsCategory) == 5


def test_llm_task_type_enum():
    assert LlmTaskType.default.value == "default"
    assert len(LlmTaskType) == 7


def test_news_table_has_indexes():
    news_table = Base.metadata.tables["news"]
    index_names = {idx.name for idx in news_table.indexes}
    assert "ix_news_status_category" in index_names
    assert "ix_news_published_at" in index_names


def test_news_url_unique():
    news_table = Base.metadata.tables["news"]
    url_col = news_table.c.url
    assert url_col.unique


def test_llm_config_task_type_unique():
    table = Base.metadata.tables["llm_configs"]
    assert table.c.task_type.unique
