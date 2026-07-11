"""Job API schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from plextraktbox.cron import validate_cron_expression
from plextraktbox.models.job import Job, NotifyMode, SourcePair
from plextraktbox.models.job_run import JobRun, JobRunStatus, RunTrigger
from plextraktbox.sync.plans import DataType
from plextraktbox.utils.datetime import UtcDatetime


class JobCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    source_pair: SourcePair
    enabled: bool = True
    cron: str = "0 3 * * *"
    dry_run: bool = False
    data_types: list[DataType] = Field(default_factory=lambda: [DataType.WATCHLIST])
    notify_mode: NotifyMode = NotifyMode.INHERIT

    @field_validator("cron")
    @classmethod
    def validate_cron(cls, value: str) -> str:
        return validate_cron_expression(value)


class JobUpdateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    source_pair: SourcePair
    enabled: bool = True
    cron: str = "0 3 * * *"
    dry_run: bool = False
    data_types: list[DataType] = Field(default_factory=lambda: [DataType.WATCHLIST])
    notify_mode: NotifyMode = NotifyMode.INHERIT

    @field_validator("cron")
    @classmethod
    def validate_cron(cls, value: str) -> str:
        return validate_cron_expression(value)


class JobResponse(BaseModel):
    id: int
    name: str
    source_pair: SourcePair
    enabled: bool
    cron: str
    dry_run: bool
    data_types: list[DataType]
    notify_mode: NotifyMode

    @classmethod
    def from_model(cls, job: Job) -> JobResponse:
        return cls(
            id=job.id or 0,
            name=job.name,
            source_pair=job.source_pair,
            enabled=job.enabled,
            cron=job.cron,
            dry_run=job.dry_run,
            data_types=sorted(job.data_types(), key=lambda dt: dt.value),
            notify_mode=job.notify_mode(),
        )


class JobRunResponse(BaseModel):
    id: int
    job_id: int
    trigger: RunTrigger
    dry_run: bool
    status: JobRunStatus
    started_at: UtcDatetime
    finished_at: UtcDatetime | None
    summary: dict[str, int]
    error: str | None

    @classmethod
    def from_model(cls, run: JobRun) -> JobRunResponse:
        return cls(
            id=run.id or 0,
            job_id=run.job_id,
            trigger=run.trigger,
            dry_run=run.dry_run,
            status=run.status,
            started_at=run.started_at,
            finished_at=run.finished_at,
            summary=run.summary().to_dict(),
            error=run.error,
        )


class JobRunRequest(BaseModel):
    dry_run: bool | None = None
