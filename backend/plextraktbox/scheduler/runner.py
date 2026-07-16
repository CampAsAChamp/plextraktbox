"""Single entry point for scheduled and manual sync job runs."""

from __future__ import annotations

import asyncio
import threading
import time
from datetime import UTC, datetime

import structlog
from sqlmodel import Session

from plextraktbox import db
from plextraktbox.config import get_settings
from plextraktbox.logging_setup import get_logger
from plextraktbox.logstream import get_log_hub
from plextraktbox.models.job import Job
from plextraktbox.models.job_run import JobRun, JobRunStatus, RunTrigger
from plextraktbox.notifications import dispatch_notifications
from plextraktbox.services import settings as settings_svc
from plextraktbox.services.dry_run import resolve_dry_run
from plextraktbox.services.source_factory import build_sources
from plextraktbox.sync.cancellation import (
    RunCancelled,
    clear_cancel_event,
    register_cancel_event,
    reset_active_cancel_event,
    set_active_cancel_event,
)
from plextraktbox.sync.context import SyncContext
from plextraktbox.sync.engine import run_sync
from plextraktbox.sync.excludes import merge_exclude_ids, normalize_exclude_ids
from plextraktbox.sync.plans import RunSummary

log = get_logger(__name__)

_job_locks: dict[int, threading.Lock] = {}
_job_locks_guard = threading.Lock()


def _apply_dev_run_delay(run_logger, cancel_event: threading.Event | None = None) -> None:
    """Sleep between log ticks so dev runs stay open long enough to test live streaming."""
    from plextraktbox.sync.cancellation import check_cancelled

    settings = get_settings()
    if settings.env != "local" or settings.sync_run_delay_seconds <= 0:
        return

    total = int(settings.sync_run_delay_seconds)
    if total <= 0:
        return

    run_logger.info("sync.run.dev_delay.start", seconds=total)
    for second in range(1, total + 1):
        check_cancelled(cancel_event)
        time.sleep(1)
        run_logger.info("sync.run.dev_delay.tick", elapsed=second, total=total)


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

    dry_run, coerced = resolve_dry_run(session, job, dry_run_override=dry_run_override)

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
    run_id_value = run.id or 0
    cancel_event = register_cancel_event(run_id_value)
    cancel_token = set_active_cancel_event(cancel_event)
    get_log_hub().open(run_id_value)
    # So client/helper loggers (e.g. plex_client apply progress) attach to this run
    # and show up in the UI log stream — not only in the process console.
    structlog.contextvars.bind_contextvars(job_id=job.id, run_id=run.id)

    final_status = JobRunStatus.FAILED.value
    try:
        _apply_dev_run_delay(run_logger, cancel_event)
        if coerced:
            run_logger.warning(
                "sync.run.dry_run_coerced",
                message=(
                    "require_dry_run_first: forcing dry-run until a successful dry-run exists for this job"
                ),
                job_name=job.name,
            )
        app_settings = settings_svc.ensure_defaults(session)
        exclude_ids = merge_exclude_ids(
            normalize_exclude_ids(app_settings.exclude_ids),
            job.exclude_ids(),
        )
        run_logger.info(
            "sync.run.start",
            message=f"Starting sync job: {job.name}",
            job_name=job.name,
            dry_run=dry_run,
            data_types=sorted(dt.value for dt in job.data_types()),
            source_pair=job.source_pair.value,
        )
        sources = build_sources(session, job, log=run_logger)
        ctx = SyncContext(
            sources=sources,
            data_types=job.data_types(),
            dry_run=dry_run,
            log=run_logger,
            exclude_ids=exclude_ids,
            cancel_event=cancel_event,
        )
        summary = asyncio.run(run_sync(ctx))
        if not _finalize_if_still_running(
            session,
            run,
            status=_status_from_summary(summary),
            summary=summary,
        ):
            run_logger.info(
                "sync.run.complete_ignored",
                reason="already_terminal",
                status=run.status.value,
            )
            final_status = run.status.value
            return run.id or 0
        final_status = run.status.value
        run_logger.info(
            "sync.run.complete",
            status=run.status.value,
            summary=summary.to_dict(),
        )
        dispatch_notifications(session, job, run)
        return run.id or 0
    except RunCancelled as exc:
        run_logger.info("sync.run.cancelled", error=str(exc))
        session.refresh(run)
        final_status = run.status.value
        if run.status == JobRunStatus.RUNNING and _finalize_if_still_running(
            session,
            run,
            status=JobRunStatus.FAILED,
            error=str(exc),
        ):
            final_status = run.status.value
            dispatch_notifications(session, job, run)
        return run.id or 0
    except Exception as exc:
        if not _finalize_if_still_running(
            session,
            run,
            status=JobRunStatus.FAILED,
            error=str(exc),
        ):
            run_logger.warning(
                "sync.run.failed_ignored",
                reason="already_terminal",
                status=run.status.value,
                error=str(exc),
            )
            final_status = run.status.value
            return run.id or 0
        final_status = run.status.value
        run_logger.warning("sync.run.failed", error=str(exc))
        dispatch_notifications(session, job, run)
        raise
    finally:
        reset_active_cancel_event(cancel_token)
        clear_cancel_event(run_id_value)
        structlog.contextvars.unbind_contextvars("job_id", "run_id")
        if run.id is not None:
            get_log_hub().close(run.id, status=final_status)


def _finalize_if_still_running(
    session: Session,
    run: JobRun,
    *,
    status: JobRunStatus,
    summary: RunSummary | None = None,
    error: str | None = None,
) -> bool:
    """Persist a terminal status only if the run is still marked running.

    Returns False when a user already marked the run failed (or it otherwise left
    running), so we do not overwrite that administrative action.
    """
    session.refresh(run)
    if run.status != JobRunStatus.RUNNING:
        return False
    if summary is not None:
        run.set_summary(summary)
    run.status = status
    run.error = error
    run.finished_at = datetime.now(UTC)
    session.add(run)
    session.commit()
    session.refresh(run)
    return True


def _status_from_summary(summary: RunSummary) -> JobRunStatus:
    if summary.errors and (summary.added or summary.removed or summary.rated or summary.watched):
        return JobRunStatus.PARTIAL
    if summary.errors:
        return JobRunStatus.FAILED
    return JobRunStatus.SUCCESS
