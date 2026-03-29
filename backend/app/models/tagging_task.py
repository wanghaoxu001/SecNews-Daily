from sqlalchemy import Boolean, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class TaggingTask(TimestampMixin, Base):
    __tablename__ = "tagging_tasks"

    original_file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="in_progress", nullable=False, index=True)
    total_count: Mapped[int] = mapped_column(Integer, nullable=False)
    current_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    imported_at: Mapped[str | None] = mapped_column(String(40), nullable=True)

    items: Mapped[list["TaggingTaskItem"]] = relationship(
        "TaggingTaskItem",
        back_populates="task",
        cascade="all, delete-orphan",
        order_by="TaggingTaskItem.row_index",
        lazy="selectin",
    )


class TaggingTaskItem(TimestampMixin, Base):
    __tablename__ = "tagging_task_items"
    __table_args__ = (
        UniqueConstraint("task_id", "row_index", name="uq_tagging_task_items_task_row"),
    )

    task_id: Mapped[int] = mapped_column(ForeignKey("tagging_tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    row_index: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_important: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    raw_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    task: Mapped[TaggingTask] = relationship("TaggingTask", back_populates="items", lazy="selectin")
