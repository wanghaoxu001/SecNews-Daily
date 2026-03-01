from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class TaskConfig(TimestampMixin, Base):
    __tablename__ = "task_configs"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    cron_expression: Mapped[str] = mapped_column(String(100), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
