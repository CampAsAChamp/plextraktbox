"""Run history API schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from plextraktbox.models.job_run import JobRun, JobRunStatus, RunTrigger


class RunListItem(BaseModel):
    id: int
    job_id: int
    job_name: str | None
    trigger: RunTrigger
    dry_run: bool
    status: JobRunStatus
    started_at: datetime
    finished_at: datetime | None
    summary: dict[str, int]
    error: str | None

    @classmethod
    def from_model(cls, run: JobRun, *, job_name: str | None = None) -> RunListItem:
        return cls(
            id=run.id or 0,
            job_id=run.job_id,
            job_name=job_name,
            trigger=run.trigger,
            dry_run=run.dry_run,
            status=run.status,
            started_at=run.started_at,
            finished_at=run.finished_at,
            summary=run.summary().to_dict(),
            error=run.error,
        )


class RunListResponse(BaseModel):
    items: list[RunListItem]
    limit: int
    offset: int
