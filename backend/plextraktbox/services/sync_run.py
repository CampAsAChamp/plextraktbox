"""Synchronous job execution — deprecated; use scheduler.runner.execute_run."""

from __future__ import annotations

from sqlmodel import Session

from plextraktbox.models.job import Job
from plextraktbox.models.job_run import JobRun, RunTrigger
from plextraktbox.scheduler.runner import execute_run


def execute_job_sync(
    session: Session,
    job: Job,
    *,
    trigger: RunTrigger = RunTrigger.MANUAL,
    dry_run_override: bool | None = None,
) -> JobRun:
    """Run a job inline (tests and legacy callers). Prefer the scheduler in production."""
    if job.id is None:
        raise ValueError("Job must be persisted before running")

    run_id = execute_run(
        job.id,
        trigger=trigger,
        dry_run_override=dry_run_override,
    )
    if run_id is None:
        raise RuntimeError(f"Job {job.id} is already running")

    run = session.get(JobRun, run_id)
    if run is None:
        raise ValueError(f"JobRun {run_id} not found")
    return run
