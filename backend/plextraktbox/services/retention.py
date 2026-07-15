"""Prune old job runs and their log entries."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlmodel import Session, select

from plextraktbox.logging_setup import get_logger
from plextraktbox.models.job_run import JobRun, JobRunStatus
from plextraktbox.models.log_entry import LogEntry
from plextraktbox.services import settings as settings_svc

log = get_logger(__name__)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def prune_old_runs(session: Session, *, retention_days: int | None = None) -> dict[str, int]:
    """Delete completed runs older than retention and their log rows.

    Running jobs are never pruned.
    """
    if retention_days is None:
        retention_days = settings_svc.ensure_defaults(session).log_retention_days
    if retention_days < 1:
        raise ValueError("retention_days must be at least 1")

    cutoff = datetime.now(UTC) - timedelta(days=retention_days)
    candidates = list(
        session.exec(
            select(JobRun).where(
                JobRun.status != JobRunStatus.RUNNING,
                JobRun.finished_at.is_not(None),  # type: ignore[union-attr]
            )
        ).all()
    )
    old_runs = [
        run for run in candidates if run.finished_at is not None and _as_utc(run.finished_at) < cutoff
    ]
    run_ids = [run.id for run in old_runs if run.id is not None]
    if not run_ids:
        return {"runs_deleted": 0, "logs_deleted": 0}

    logs_deleted = 0
    for run_id in run_ids:
        log_rows = list(session.exec(select(LogEntry).where(LogEntry.run_id == run_id)).all())
        for row in log_rows:
            session.delete(row)
            logs_deleted += 1

    for run in old_runs:
        session.delete(run)
    session.commit()

    log.info(
        "retention.pruned",
        runs_deleted=len(run_ids),
        logs_deleted=logs_deleted,
        retention_days=retention_days,
        cutoff=cutoff.isoformat(),
    )
    return {"runs_deleted": len(run_ids), "logs_deleted": logs_deleted}
