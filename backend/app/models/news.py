from datetime import datetime

from sqlalchemy import String, Text, Boolean, Integer, ForeignKey, Index, JSON, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from app.models.base import Base, TimestampMixin
from app.models.enums import ProcessStatus, NewsCategory


class News(TimestampMixin, Base):
    __tablename__ = "news"

    # Original content
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    url: Mapped[str] = mapped_column(String(1000), unique=True, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    author: Mapped[str | None] = mapped_column(String(200), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Source
    source_id: Mapped[int | None] = mapped_column(ForeignKey("rss_sources.id"), nullable=True)
    source_name: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # Translated / processed content
    title_zh: Mapped[str | None] = mapped_column(String(500), nullable=True)
    summary_zh: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Classification
    category: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Processing state
    process_status: Mapped[str] = mapped_column(
        String(30), default=ProcessStatus.pending.value, index=True
    )
    process_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Embedding
    embedding: Mapped[list | None] = mapped_column(Vector(1536), nullable=True)

    # Similarity
    is_similar: Mapped[bool] = mapped_column(Boolean, default=False)
    similar_to_id: Mapped[int | None] = mapped_column(ForeignKey("news.id"), nullable=True)
    similarity_details: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Importance
    is_important: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    importance_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    source: Mapped["RssSource | None"] = relationship("RssSource", lazy="selectin")
    similar_to: Mapped["News | None"] = relationship("News", remote_side="News.id", lazy="selectin")

    __table_args__ = (
        Index("ix_news_status_category", "process_status", "category"),
        Index("ix_news_published_at", "published_at"),
    )
