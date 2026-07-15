"""Dry-run resolution and first-run safety guards."""

from __future__ import annotations

from sqlmodel import Session, select

from plextraktbox.models.job import Job
from plextraktbox.models.job_run import JobRun, JobRunStatus


def has_successful_dry_run(session: Session, job_id: int) -> bool:
    statement = (
        select(JobRun)
        .where(
            JobRun.job_id == job_id,
            JobRun.dry_run.is_(True),  # type: ignore[attr-defined]
            JobRun.status == JobRunStatus.SUCCESS,
        )
        .limit(1)
    )
    return session.exec(statement).first() is not None


def resolve_dry_run(
    session: Session,
    job: Job,
    *,
    dry_run_override: bool | None,
) -> tuple[bool, bool]:
    """Return ``(dry_run, coerced_by_first_run_guard)``.

    Resolution: ``override ?? job.dry_run``. When ``require_dry_run_first`` is set
    and no successful dry-run exists yet for the job, a live run is coerced to
    dry-run so unattended schedules stay safe.
    """
    dry_run = job.dry_run if dry_run_override is None else dry_run_override
    if dry_run:
        return True, False
    if not job.require_dry_run_first:
        return False, False
    if job.id is None:
        return True, True
    if has_successful_dry_run(session, job.id):
        return False, False
    return True, True
