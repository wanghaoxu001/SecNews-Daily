from sqlalchemy import String, Text, Float
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class LlmConfig(TimestampMixin, Base):
    __tablename__ = "llm_configs"

    task_type: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    base_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    api_key: Mapped[str | None] = mapped_column(String(500), nullable=True)
    model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    temperature: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_tokens: Mapped[int | None] = mapped_column(nullable=True)
