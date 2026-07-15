"""Log/run retention pruning tests."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlmodel import Session, select

from plextraktbox.models.job_run import JobRun, JobRunStatus, RunTrigger
from plextraktbox.models.log_entry import LogEntry
from plextraktbox.services.retention import prune_old_runs


def test_prune_old_runs_keeps_running_and_recent(session: Session) -> None:
    old = JobRun(
        job_id=1,
        job_name="old",
        trigger=RunTrigger.MANUAL,
        dry_run=True,
        status=JobRunStatus.SUCCESS,
        started_at=datetime.now(UTC) - timedelta(days=40),
        finished_at=datetime.now(UTC) - timedelta(days=40),
    )
    recent = JobRun(
        job_id=1,
        job_name="recent",
        trigger=RunTrigger.MANUAL,
        dry_run=True,
        status=JobRunStatus.SUCCESS,
        started_at=datetime.now(UTC) - timedelta(days=2),
        finished_at=datetime.now(UTC) - timedelta(days=2),
    )
    running = JobRun(
        job_id=1,
        job_name="running",
        trigger=RunTrigger.MANUAL,
        dry_run=True,
        status=JobRunStatus.RUNNING,
        started_at=datetime.now(UTC) - timedelta(days=40),
        finished_at=None,
    )
    session.add(old)
    session.add(recent)
    session.add(running)
    session.commit()
    session.refresh(old)
    session.refresh(recent)
    session.refresh(running)

    session.add(LogEntry(run_id=old.id or 0, message="old log"))
    session.add(LogEntry(run_id=recent.id or 0, message="recent log"))
    session.commit()

    result = prune_old_runs(session, retention_days=30)
    assert result["runs_deleted"] == 1
    assert result["logs_deleted"] == 1

    remaining = list(session.exec(select(JobRun)).all())
    assert {run.job_name for run in remaining} == {"recent", "running"}
    logs = list(session.exec(select(LogEntry)).all())
    assert len(logs) == 1
    assert logs[0].message == "recent log"
