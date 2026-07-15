"""Dev run delay helper tests."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

from sqlmodel import Session

from plextraktbox.models.job_run import JobRun, JobRunStatus, RunTrigger
from plextraktbox.scheduler.runner import _apply_dev_run_delay, _finalize_if_still_running
from plextraktbox.services.runs import MARKED_FAILED_ERROR, mark_run_failed
from plextraktbox.sync.plans import RunSummary


def test_dev_run_delay_skipped_in_prod() -> None:
    logger = MagicMock()
    with patch("plextraktbox.scheduler.runner.get_settings") as get_settings:
        get_settings.return_value.env = "prod"
        get_settings.return_value.sync_run_delay_seconds = 10
        with patch("plextraktbox.scheduler.runner.time.sleep") as sleep:
            _apply_dev_run_delay(logger)

    sleep.assert_not_called()
    logger.info.assert_not_called()


def test_dev_run_delay_skipped_when_zero() -> None:
    logger = MagicMock()
    with patch("plextraktbox.scheduler.runner.get_settings") as get_settings:
        get_settings.return_value.env = "dev"
        get_settings.return_value.sync_run_delay_seconds = 0
        with patch("plextraktbox.scheduler.runner.time.sleep") as sleep:
            _apply_dev_run_delay(logger)

    sleep.assert_not_called()
    logger.info.assert_not_called()


def test_dev_run_delay_logs_and_sleeps_each_second() -> None:
    logger = MagicMock()
    with patch("plextraktbox.scheduler.runner.get_settings") as get_settings:
        get_settings.return_value.env = "dev"
        get_settings.return_value.sync_run_delay_seconds = 3
        with patch("plextraktbox.scheduler.runner.time.sleep") as sleep:
            _apply_dev_run_delay(logger)

    assert sleep.call_count == 3
    logger.info.assert_any_call("sync.run.dev_delay.start", seconds=3)
    logger.info.assert_any_call("sync.run.dev_delay.tick", elapsed=1, total=3)
    logger.info.assert_any_call("sync.run.dev_delay.tick", elapsed=3, total=3)


def test_finalize_skips_when_user_marked_failed(session: Session) -> None:
    run = JobRun(
        job_id=1,
        job_name="Guard test",
        trigger=RunTrigger.MANUAL,
        dry_run=True,
        status=JobRunStatus.RUNNING,
        started_at=datetime.now(UTC),
    )
    session.add(run)
    session.commit()
    session.refresh(run)

    mark_run_failed(session, run)

    ok = _finalize_if_still_running(
        session,
        run,
        status=JobRunStatus.SUCCESS,
        summary=RunSummary(matched=1),
    )
    assert ok is False
    session.refresh(run)
    assert run.status == JobRunStatus.FAILED
    assert run.error == MARKED_FAILED_ERROR


def test_finalize_commits_when_still_running(session: Session) -> None:
    run = JobRun(
        job_id=1,
        job_name="Guard test",
        trigger=RunTrigger.MANUAL,
        dry_run=True,
        status=JobRunStatus.RUNNING,
        started_at=datetime.now(UTC),
    )
    session.add(run)
    session.commit()
    session.refresh(run)

    ok = _finalize_if_still_running(
        session,
        run,
        status=JobRunStatus.SUCCESS,
        summary=RunSummary(matched=2),
    )
    assert ok is True
    session.refresh(run)
    assert run.status == JobRunStatus.SUCCESS
    assert run.finished_at is not None
    assert run.summary().matched == 2
