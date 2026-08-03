from datetime import datetime
from enum import StrEnum

from pydantic import Field

from .common import StrictModel, utc_now


class RunStatus(StrEnum):
    RUNNING = "running"
    STOPPED = "stopped"
    COMPLETED = "completed"
    FAILED = "failed"


class RunState(StrictModel):
    run_id: str
    status: RunStatus = RunStatus.RUNNING
    provider: str
    total_units: int
    completed_units: int = 0
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
