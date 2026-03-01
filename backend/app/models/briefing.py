from datetime import datetime

from sqlalchemy import String, Text, Integer, ForeignKey, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import BriefingStatus


class Briefing(TimestampMixin, Base):
    __tablename__ = "briefings"

    title: Mapped[str] = mapped_column(String(300), nullable=False)
    date: Mapped[datetime] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default=BriefingStatus.draft.value)

    items: Mapped[list["BriefingItem"]] = relationship(
        "BriefingItem", back_populates="briefing", cascade="all, delete-orphan",
        order_by="BriefingItem.sort_order", lazy="selectin"
    )


class BriefingItem(TimestampMixin, Base):
    __tablename__ = "briefing_items"

    briefing_id: Mapped[int] = mapped_column(ForeignKey("briefings.id", ondelete="CASCADE"), nullable=False)
    news_id: Mapped[int | None] = mapped_column(ForeignKey("news.id"), nullable=True)

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    briefing: Mapped["Briefing"] = relationship("Briefing", back_populates="items")
    news: Mapped["News | None"] = relationship("News", lazy="selectin")
