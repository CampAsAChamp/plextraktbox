"""Job API schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from plextraktbox.cron import validate_cron_expression
from plextraktbox.models.job import Job, NotifyMode, SourcePair
from plextraktbox.models.job_run import JobRun, JobRunStatus, RunTrigger
from plextraktbox.schemas.run import RunSummaryOut
from plextraktbox.schemas.settings import ExcludeIds
from plextraktbox.sync.excludes import EXCLUDE_ID_KEYS, dump_exclude_ids, normalize_exclude_ids
from plextraktbox.sync.plans import DataType
from plextraktbox.utils.datetime import UtcDatetime


class JobCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    source_pair: SourcePair
    enabled: bool = True
    cron: str | None = None
    dry_run: bool | None = None
    require_dry_run_first: bool = True
    data_types: list[DataType] = Field(default_factory=lambda: [DataType.WATCHLIST])
    notify_mode: NotifyMode = NotifyMode.INHERIT
    exclude_ids: ExcludeIds = Field(default_factory=ExcludeIds)

    @field_validator("cron")
    @classmethod
    def validate_cron(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return validate_cron_expression(value)


class JobUpdateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    source_pair: SourcePair
    enabled: bool = True
    cron: str = "0 3 * * *"
    dry_run: bool = False
    require_dry_run_first: bool = True
    data_types: list[DataType] = Field(default_factory=lambda: [DataType.WATCHLIST])
    notify_mode: NotifyMode = NotifyMode.INHERIT
    exclude_ids: ExcludeIds = Field(default_factory=ExcludeIds)

    @field_validator("cron")
    @classmethod
    def validate_cron(cls, value: str) -> str:
        return validate_cron_expression(value)


class SchedulePreviewRequest(BaseModel):
    cron: str
    count: int = Field(default=5, ge=1, le=20)

    @field_validator("cron")
    @classmethod
    def validate_cron(cls, value: str) -> str:
        return validate_cron_expression(value)


class SchedulePreviewResponse(BaseModel):
    times: list[UtcDatetime]


class JobLastRun(BaseModel):
    """Compact latest-run snapshot for job list / dashboard ops."""

    id: int
    status: JobRunStatus
    dry_run: bool
    started_at: UtcDatetime
    finished_at: UtcDatetime | None
    matched: int
    added: int
    errors: int

    @classmethod
    def from_model(cls, run: JobRun) -> JobLastRun:
        summary = run.summary()
        return cls(
            id=run.id or 0,
            status=run.status,
            dry_run=run.dry_run,
            started_at=run.started_at,
            finished_at=run.finished_at,
            matched=summary.matched,
            added=summary.added,
            errors=summary.errors,
        )


class JobResponse(BaseModel):
    id: int
    name: str
    source_pair: SourcePair
    enabled: bool
    cron: str
    dry_run: bool
    require_dry_run_first: bool
    data_types: list[DataType]
    notify_mode: NotifyMode
    exclude_ids: ExcludeIds
    next_run_at: UtcDatetime | None = None
    last_run: JobLastRun | None = None

    @classmethod
    def from_model(
        cls,
        job: Job,
        *,
        next_run_at: UtcDatetime | None = None,
        last_run: JobLastRun | None = None,
    ) -> JobResponse:
        normalized = dump_exclude_ids(job.exclude_ids())
        return cls(
            id=job.id or 0,
            name=job.name,
            source_pair=job.source_pair,
            enabled=job.enabled,
            cron=job.cron,
            dry_run=job.dry_run,
            require_dry_run_first=job.require_dry_run_first,
            data_types=sorted(job.data_types(), key=lambda dt: dt.value),
            notify_mode=job.notify_mode(),
            exclude_ids=ExcludeIds(
                tmdb=normalized.get("tmdb", []),
                imdb=normalized.get("imdb", []),
                tvdb=normalized.get("tvdb", []),
            ),
            next_run_at=next_run_at,
            last_run=last_run,
        )


class JobRunResponse(BaseModel):
    id: int
    job_id: int
    trigger: RunTrigger
    dry_run: bool
    status: JobRunStatus
    started_at: UtcDatetime
    finished_at: UtcDatetime | None
    summary: RunSummaryOut
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
            summary=RunSummaryOut.model_validate(run.summary().to_dict()),
            error=run.error,
        )


class JobRunRequest(BaseModel):
    dry_run: bool | None = None


def exclude_ids_from_request(exclude_ids: ExcludeIds) -> dict[str, list[str]]:
    raw = {key: getattr(exclude_ids, key) for key in EXCLUDE_ID_KEYS}
    return dump_exclude_ids(normalize_exclude_ids(raw))
