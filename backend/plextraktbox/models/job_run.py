"""Recorded sync job executions."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from sqlmodel import Field, SQLModel

from plextraktbox.sync.plans import RunSummary


class RunTrigger(StrEnum):
    SCHEDULED = "scheduled"
    MANUAL = "manual"


class JobRunStatus(StrEnum):
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"


class JobRun(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    job_id: int = Field(index=True)
    trigger: RunTrigger = Field(default=RunTrigger.MANUAL)
    dry_run: bool = Field(default=False)
    status: JobRunStatus = Field(default=JobRunStatus.RUNNING, index=True)
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    finished_at: datetime | None = Field(default=None, nullable=True)
    summary_json: str = Field(default="{}")
    error: str | None = Field(default=None, nullable=True)

    def summary(self) -> RunSummary:
        try:
            raw: dict[str, Any] = json.loads(self.summary_json)
        except json.JSONDecodeError:
            return RunSummary()
        return RunSummary(
            matched=int(raw.get("matched", 0)),
            added=int(raw.get("added", 0)),
            removed=int(raw.get("removed", 0)),
            rated=int(raw.get("rated", 0)),
            watched=int(raw.get("watched", 0)),
            skipped=int(raw.get("skipped", 0)),
            errors=int(raw.get("errors", 0)),
            planned=int(raw.get("planned", 0)),
        )

    def set_summary(self, summary: RunSummary) -> None:
        self.summary_json = json.dumps(summary.to_dict())
