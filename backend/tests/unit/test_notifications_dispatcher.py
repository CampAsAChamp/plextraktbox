"""Notification dispatcher tests."""

from __future__ import annotations

from datetime import UTC, datetime

import httpx
import pytest
import respx
from sqlmodel import Session, select

from plextraktbox.models.inapp_notification import InAppNotification
from plextraktbox.models.job import Job, NotifyMode, SourcePair
from plextraktbox.models.job_run import JobRun, JobRunStatus, RunTrigger
from plextraktbox.models.notification_config import (
    NotificationChannel,
    NotificationConfig,
    NotificationScope,
)
from plextraktbox.notifications.dispatcher import (
    build_payload,
    dispatch_notifications,
    resolve_configs,
)
from plextraktbox.security import encrypt_secret


def _job(**overrides) -> Job:
    defaults = {
        "id": 1,
        "name": "Plex ↔ Trakt",
        "source_pair": SourcePair.PLEX_TRAKT,
        "notify_override_json": Job.dump_notify_mode(NotifyMode.INHERIT),
    }
    defaults.update(overrides)
    return Job(**defaults)


def _run(**overrides) -> JobRun:
    defaults = {
        "id": 10,
        "job_id": 1,
        "job_name": "Plex ↔ Trakt",
        "trigger": RunTrigger.MANUAL,
        "dry_run": False,
        "status": JobRunStatus.SUCCESS,
        "started_at": datetime(2026, 7, 11, 12, 0, tzinfo=UTC),
        "finished_at": datetime(2026, 7, 11, 12, 0, 5, tzinfo=UTC),
        "summary_json": '{"matched": 3, "added": 1}',
    }
    defaults.update(overrides)
    return JobRun(**defaults)


def test_build_payload_includes_duration_and_run_url() -> None:
    payload = build_payload(_job(), _run())
    assert payload.duration_seconds == pytest.approx(5.0)
    assert payload.run_url == "/#/runs/10"
    assert payload.status == "success"


def test_resolve_configs_respects_notify_mode(session: Session) -> None:
    job = _job(notify_override_json=Job.dump_notify_mode(NotifyMode.DISABLED))
    session.add(
        NotificationConfig(
            channel=NotificationChannel.INAPP,
            enabled=True,
            on_success=True,
            on_failure=True,
            scope=NotificationScope.GLOBAL,
        )
    )
    session.commit()

    assert resolve_configs(session, job, JobRunStatus.SUCCESS) == []


def test_resolve_configs_uses_global_on_inherit(session: Session) -> None:
    job = _job()
    config = NotificationConfig(
        channel=NotificationChannel.INAPP,
        enabled=True,
        on_success=True,
        on_failure=False,
        scope=NotificationScope.GLOBAL,
    )
    session.add(config)
    session.commit()
    session.refresh(config)

    matched = resolve_configs(session, job, JobRunStatus.SUCCESS)
    assert len(matched) == 1
    assert matched[0].id == config.id

    assert resolve_configs(session, job, JobRunStatus.FAILED) == []


def test_resolve_configs_uses_job_scope_for_custom(session: Session) -> None:
    job = _job(notify_override_json=Job.dump_notify_mode(NotifyMode.CUSTOM))
    session.add(job)
    session.commit()
    session.refresh(job)

    global_config = NotificationConfig(
        channel=NotificationChannel.INAPP,
        enabled=True,
        on_success=True,
        on_failure=True,
        scope=NotificationScope.GLOBAL,
    )
    job_config = NotificationConfig(
        channel=NotificationChannel.INAPP,
        enabled=True,
        on_success=True,
        on_failure=True,
        scope=NotificationScope.JOB,
        job_id=job.id,
    )
    session.add(global_config)
    session.add(job_config)
    session.commit()
    session.refresh(job_config)

    matched = resolve_configs(session, job, JobRunStatus.SUCCESS)
    assert len(matched) == 1
    assert matched[0].id == job_config.id


@respx.mock
def test_dispatch_notifications_inserts_inapp_row(session: Session) -> None:
    job = _job()
    session.add(job)
    session.commit()
    session.refresh(job)

    session.add(
        NotificationConfig(
            channel=NotificationChannel.INAPP,
            enabled=True,
            on_success=True,
            on_failure=True,
            scope=NotificationScope.GLOBAL,
        )
    )
    session.commit()

    run = _run(job_id=job.id or 0)
    session.add(run)
    session.commit()
    session.refresh(run)

    dispatch_notifications(session, job, run)

    rows = list(session.exec(select(InAppNotification)).all())
    assert len(rows) == 1
    assert rows[0].title.startswith("Plex ↔ Trakt")


@respx.mock
def test_dispatch_notifications_sends_discord_webhook(session: Session) -> None:
    route = respx.post("https://discord.test/webhook").mock(return_value=httpx.Response(204))
    job = _job()
    session.add(job)
    session.commit()
    session.refresh(job)

    session.add(
        NotificationConfig(
            channel=NotificationChannel.DISCORD,
            enabled=True,
            on_success=True,
            on_failure=True,
            scope=NotificationScope.GLOBAL,
            config_enc=encrypt_secret("https://discord.test/webhook"),
        )
    )
    session.commit()

    run = _run(job_id=job.id or 0)
    session.add(run)
    session.commit()
    session.refresh(run)

    dispatch_notifications(session, job, run)

    assert route.called
