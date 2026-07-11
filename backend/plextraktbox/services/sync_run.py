"""Synchronous job execution (Phase 3 temporary runner; scheduler in Phase 4)."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime

from sqlmodel import Session

from plextraktbox.logging_setup import get_logger
from plextraktbox.models.job import Job
from plextraktbox.models.job_run import JobRun, JobRunStatus, RunTrigger
from plextraktbox.services.source_factory import build_sources
from plextraktbox.sync.context import SyncContext
from plextraktbox.sync.engine import run_sync
from plextraktbox.sync.plans import RunSummary

log = get_logger(__name__)


def execute_job_sync(
    session: Session,
    job: Job,
    *,
    trigger: RunTrigger = RunTrigger.MANUAL,
    dry_run_override: bool | None = None,
) -> JobRun:
    dry_run = job.dry_run if dry_run_override is None else dry_run_override
    run = JobRun(job_id=job.id or 0, trigger=trigger, dry_run=dry_run)
    session.add(run)
    session.commit()
    session.refresh(run)

    try:
        sources = build_sources(session, job)
        ctx = SyncContext(
            sources=sources,
            data_types=job.data_types(),
            dry_run=dry_run,
            log=log.bind(job_id=job.id, run_id=run.id),
        )
        summary = asyncio.run(run_sync(ctx))
        run.set_summary(summary)
        run.status = _status_from_summary(summary)
        run.finished_at = datetime.now(UTC)
        session.add(run)
        session.commit()
        session.refresh(run)
        log.info(
            "sync.run.complete",
            job_id=job.id,
            run_id=run.id,
            status=run.status.value,
            summary=summary.to_dict(),
        )
        return run
    except Exception as exc:
        run.status = JobRunStatus.FAILED
        run.error = str(exc)
        run.finished_at = datetime.now(UTC)
        session.add(run)
        session.commit()
        session.refresh(run)
        log.warning("sync.run.failed", job_id=job.id, run_id=run.id, error=str(exc))
        raise


def _status_from_summary(summary: RunSummary) -> JobRunStatus:
    if summary.errors and (summary.added or summary.removed or summary.rated or summary.watched):
        return JobRunStatus.PARTIAL
    if summary.errors:
        return JobRunStatus.FAILED
    return JobRunStatus.SUCCESS
