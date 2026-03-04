from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class CrawlDomainPolicy(TimestampMixin, Base):
    __tablename__ = "crawl_domain_policies"

    domain: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    wait_for_chain: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    timeouts_ms: Mapped[list[int] | None] = mapped_column(JSON, nullable=True)
    simulate_user: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    magic: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    probe_status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    probe_sample_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    probe_success_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    probe_avg_duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    probe_last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    probe_last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
