from datetime import datetime

from pydantic import BaseModel


class CrawlPolicyResponse(BaseModel):
    domain: str
    wait_for_chain: list[str] | None = None
    timeouts_ms: list[int] | None = None
    simulate_user: bool | None = None
    magic: bool | None = None
    probe_status: str
    probe_sample_size: int | None = None
    probe_success_rate: float | None = None
    probe_avg_duration_ms: int | None = None
    probe_last_error: str | None = None
    probe_last_run_at: datetime | None = None
    effective_wait_for_chain: list[str]
    effective_timeouts_ms: list[int]
    effective_source: str
