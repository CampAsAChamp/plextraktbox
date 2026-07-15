"""Job run query helpers."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlmodel import Session, col, select

from plextraktbox.logging_setup import get_logger
from plextraktbox.logstream import get_log_hub
from plextraktbox.models.job import Job, SourcePair
from plextraktbox.models.job_run import JobRun, JobRunStatus

log = get_logger(__name__)

MARKED_FAILED_ERROR = "Marked as failed by user"


def list_runs(
    session: Session,
    *,
    job_id: int | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[JobRun]:
    stmt = select(JobRun).order_by(col(JobRun.started_at).desc(), col(JobRun.id).desc())
    if job_id is not None:
        stmt = stmt.where(JobRun.job_id == job_id)
    stmt = stmt.offset(offset).limit(limit)
    return list(session.exec(stmt).all())


def latest_runs_by_job_ids(session: Session, job_ids: list[int]) -> dict[int, JobRun]:
    """Return the most recent JobRun for each job id (one query, first-per-job)."""
    if not job_ids:
        return {}
    stmt = (
        select(JobRun)
        .where(col(JobRun.job_id).in_(job_ids))
        .order_by(col(JobRun.started_at).desc(), col(JobRun.id).desc())
    )
    latest: dict[int, JobRun] = {}
    for run in session.exec(stmt).all():
        if run.job_id not in latest:
            latest[run.job_id] = run
            if len(latest) == len(job_ids):
                break
    return latest


def get_run(session: Session, run_id: int) -> JobRun | None:
    return session.get(JobRun, run_id)


def get_job_name(session: Session, job_id: int) -> str | None:
    job = session.get(Job, job_id)
    return job.name if job is not None else None


def get_job_source_pair(session: Session, job_id: int) -> SourcePair | None:
    job = session.get(Job, job_id)
    return job.source_pair if job is not None else None


def resolve_job_name(session: Session, run: JobRun) -> str | None:
    if run.job_name:
        return run.job_name
    return get_job_name(session, run.job_id)


def mark_run_failed(session: Session, run: JobRun) -> JobRun:
    """Mark a stuck/running run as failed. Does not interrupt an in-flight sync worker."""
    if run.status != JobRunStatus.RUNNING:
        raise ValueError(f"Run {run.id} is not running (status={run.status.value})")

    run.status = JobRunStatus.FAILED
    run.error = MARKED_FAILED_ERROR
    run.finished_at = datetime.now(UTC)
    session.add(run)
    session.commit()
    session.refresh(run)

    run_id = run.id or 0
    log.info(
        "sync.run.marked_failed",
        run_id=run_id,
        job_id=run.job_id,
        message=MARKED_FAILED_ERROR,
    )
    get_log_hub().close(run_id, status=JobRunStatus.FAILED.value)
    return run
