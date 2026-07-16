"""Run history API schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field

from plextraktbox.models.job import SourcePair
from plextraktbox.models.job_run import JobRun, JobRunStatus, RunTrigger
from plextraktbox.utils.datetime import UtcDatetime


class UnmatchedItemOut(BaseModel):
    source: str
    data_type: str
    title: str
    source_key: str
    reason: str
    identifiers: dict[str, str] = Field(default_factory=dict)


class RunSummaryOut(BaseModel):
    matched: int = 0
    added: int = 0
    removed: int = 0
    rated: int = 0
    watched: int = 0
    skipped: int = 0
    errors: int = 0
    planned: int = 0
    shows_added: int = 0
    shows_removed: int = 0
    episodes_watched: int = 0
    unmatched_count: int = 0
    unmatched: list[UnmatchedItemOut] = Field(default_factory=list)


class RunListItem(BaseModel):
    id: int
    job_id: int
    job_name: str | None
    source_pair: SourcePair | None
    trigger: RunTrigger
    dry_run: bool
    status: JobRunStatus
    started_at: UtcDatetime
    finished_at: UtcDatetime | None
    summary: RunSummaryOut
    error: str | None

    @classmethod
    def from_model(
        cls,
        run: JobRun,
        *,
        job_name: str | None = None,
        source_pair: SourcePair | None = None,
    ) -> RunListItem:
        return cls(
            id=run.id or 0,
            job_id=run.job_id,
            job_name=job_name,
            source_pair=source_pair,
            trigger=run.trigger,
            dry_run=run.dry_run,
            status=run.status,
            started_at=run.started_at,
            finished_at=run.finished_at,
            summary=RunSummaryOut.model_validate(run.summary().to_dict()),
            error=run.error,
        )


class RunListResponse(BaseModel):
    items: list[RunListItem]
    limit: int
    offset: int
