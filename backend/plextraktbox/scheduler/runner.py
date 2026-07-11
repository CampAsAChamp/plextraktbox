"""Single entry point for scheduled and manual sync job runs."""

from __future__ import annotations

import asyncio
import threading
from datetime import UTC, datetime

from sqlmodel import Session

from plextraktbox import db
from plextraktbox.logging_setup import get_logger
from plextraktbox.models.job import Job
from plextraktbox.models.job_run import JobRun, JobRunStatus, RunTrigger
from plextraktbox.services.source_factory import build_sources
from plextraktbox.sync.context import SyncContext
from plextraktbox.sync.engine import run_sync
from plextraktbox.sync.plans import RunSummary

log = get_logger(__name__)

_job_locks: dict[int, threading.Lock] = {}
_job_locks_guard = threading.Lock()


def _get_job_lock(job_id: int) -> threading.Lock:
    with _job_locks_guard:
        lock = _job_locks.get(job_id)
        if lock is None:
            lock = threading.Lock()
            _job_locks[job_id] = lock
        return lock


def execute_run(
    job_id: int,
    *,
    trigger: RunTrigger,
    dry_run_override: bool | None = None,
    run_id: int | None = None,
) -> int | None:
    """Run a sync job. Returns the JobRun id, or None if the job was already running."""
    lock = _get_job_lock(job_id)
    if not lock.acquire(blocking=False):
        log.warning("sync.run.skipped", job_id=job_id, reason="already_running")
        return None

    try:
        with Session(db.engine) as session:
            return _execute_run_in_session(
                session,
                job_id,
                trigger=trigger,
                dry_run_override=dry_run_override,
                run_id=run_id,
            )
    finally:
        lock.release()


def _execute_run_in_session(
    session: Session,
    job_id: int,
    *,
    trigger: RunTrigger,
    dry_run_override: bool | None,
    run_id: int | None,
) -> int:
    job = session.get(Job, job_id)
    if job is None:
        raise ValueError(f"Job {job_id} not found")

    dry_run = job.dry_run if dry_run_override is None else dry_run_override

    if run_id is not None:
        run = session.get(JobRun, run_id)
        if run is None:
            raise ValueError(f"JobRun {run_id} not found")
        if run.job_id != job_id:
            raise ValueError(f"JobRun {run_id} does not belong to job {job_id}")
        run.trigger = trigger
        run.dry_run = dry_run
        run.status = JobRunStatus.RUNNING
        run.error = None
        run.finished_at = None
        session.add(run)
        session.commit()
        session.refresh(run)
    else:
        run = JobRun(job_id=job_id, job_name=job.name, trigger=trigger, dry_run=dry_run)
        session.add(run)
        session.commit()
        session.refresh(run)

    run_logger = log.bind(job_id=job.id, run_id=run.id)

    try:
        sources = build_sources(session, job)
        ctx = SyncContext(
            sources=sources,
            data_types=job.data_types(),
            dry_run=dry_run,
            log=run_logger,
        )
        summary = asyncio.run(run_sync(ctx))
        run.set_summary(summary)
        run.status = _status_from_summary(summary)
        run.finished_at = datetime.now(UTC)
        session.add(run)
        session.commit()
        session.refresh(run)
        run_logger.info(
            "sync.run.complete",
            status=run.status.value,
            summary=summary.to_dict(),
        )
        return run.id or 0
    except Exception as exc:
        run.status = JobRunStatus.FAILED
        run.error = str(exc)
        run.finished_at = datetime.now(UTC)
        session.add(run)
        session.commit()
        session.refresh(run)
        run_logger.warning("sync.run.failed", error=str(exc))
        raise


def _status_from_summary(summary: RunSummary) -> JobRunStatus:
    if summary.errors and (summary.added or summary.removed or summary.rated or summary.watched):
        return JobRunStatus.PARTIAL
    if summary.errors:
        return JobRunStatus.FAILED
    return JobRunStatus.SUCCESS
