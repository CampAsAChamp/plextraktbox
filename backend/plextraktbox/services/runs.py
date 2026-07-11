"""Job run query helpers."""

from __future__ import annotations

from sqlmodel import Session, col, select

from plextraktbox.models.job import Job
from plextraktbox.models.job_run import JobRun


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


def get_run(session: Session, run_id: int) -> JobRun | None:
    return session.get(JobRun, run_id)


def get_job_name(session: Session, job_id: int) -> str | None:
    job = session.get(Job, job_id)
    return job.name if job is not None else None


def resolve_job_name(session: Session, run: JobRun) -> str | None:
    if run.job_name:
        return run.job_name
    return get_job_name(session, run.job_id)
