"""Fan-out notifications after a job run completes."""

from __future__ import annotations

import asyncio

from sqlmodel import Session, select

from plextraktbox.logging_setup import get_logger
from plextraktbox.models.inapp_notification import InAppNotification
from plextraktbox.models.job import Job, NotifyMode
from plextraktbox.models.job_run import JobRun, JobRunStatus
from plextraktbox.models.notification_config import NotificationChannel, NotificationConfig, NotificationScope
from plextraktbox.notifications.discord import send_discord
from plextraktbox.notifications.inapp import send_inapp
from plextraktbox.notifications.payload import NotificationPayload

log = get_logger(__name__)


def build_payload(job: Job, run: JobRun) -> NotificationPayload:
    duration: float | None = None
    if run.finished_at is not None:
        duration = (run.finished_at - run.started_at).total_seconds()
    return NotificationPayload(
        job_id=job.id or 0,
        job_name=run.job_name or job.name,
        run_id=run.id or 0,
        status=run.status.value,
        dry_run=run.dry_run,
        trigger=run.trigger.value,
        summary=run.summary().to_dict(),
        duration_seconds=duration,
        error=run.error,
        run_url=f"/#/runs/{run.id}",
    )


def build_test_payload(job_name: str = "Test Job") -> NotificationPayload:
    return NotificationPayload(
        job_id=0,
        job_name=job_name,
        run_id=0,
        status="success",
        dry_run=True,
        trigger="manual",
        summary={
            "matched": 12,
            "added": 2,
            "removed": 1,
            "rated": 0,
            "watched": 3,
            "skipped": 0,
            "errors": 0,
            "planned": 6,
        },
        duration_seconds=4.2,
        error=None,
        run_url="/#/runs/0",
    )


def _matches_status(config: NotificationConfig, status: JobRunStatus) -> bool:
    if status == JobRunStatus.SUCCESS:
        return config.on_success
    if status == JobRunStatus.FAILED:
        return config.on_failure
    if status == JobRunStatus.PARTIAL:
        return config.on_success or config.on_failure
    return False


def resolve_configs(session: Session, job: Job, status: JobRunStatus) -> list[NotificationConfig]:
    mode = job.notify_mode()
    if mode == NotifyMode.DISABLED:
        return []

    scope = NotificationScope.GLOBAL if mode == NotifyMode.INHERIT else NotificationScope.JOB
    statement = select(NotificationConfig).where(
        NotificationConfig.scope == scope,
        NotificationConfig.enabled.is_(True),  # type: ignore[attr-defined]
    )
    if scope == NotificationScope.JOB:
        statement = statement.where(NotificationConfig.job_id == job.id)

    configs = list(session.exec(statement).all())
    return [config for config in configs if _matches_status(config, status)]


async def _dispatch_one(
    session: Session,
    config: NotificationConfig,
    payload: NotificationPayload,
) -> None:
    if config.channel == NotificationChannel.DISCORD:
        await send_discord(config, payload)
    elif config.channel == NotificationChannel.INAPP:
        await send_inapp(session, config, payload)
    else:
        raise ValueError(f"Unsupported notification channel: {config.channel}")


async def dispatch_payload(
    session: Session,
    configs: list[NotificationConfig],
    payload: NotificationPayload,
) -> None:
    if not configs:
        return

    async def _safe_send(config: NotificationConfig) -> None:
        try:
            await _dispatch_one(session, config, payload)
        except Exception as exc:
            log.warning(
                "notification.dispatch.failed",
                channel=config.channel.value,
                config_id=config.id,
                error=str(exc),
            )

    await asyncio.gather(*(_safe_send(config) for config in configs))


def dispatch_notifications(session: Session, job: Job, run: JobRun) -> None:
    """Send notifications for a completed run. Failures are logged, never raised."""
    if run.status == JobRunStatus.RUNNING:
        return
    configs = resolve_configs(session, job, run.status)
    if not configs:
        return
    payload = build_payload(job, run)
    try:
        asyncio.run(dispatch_payload(session, configs, payload))
    except Exception as exc:
        log.warning("notification.dispatch.failed", error=str(exc), run_id=run.id)


async def send_test_notification(session: Session, config: NotificationConfig) -> None:
    payload = build_test_payload()
    await _dispatch_one(session, config, payload)


def list_inapp_notifications(
    session: Session,
    *,
    limit: int = 50,
    unread_only: bool = False,
) -> list[InAppNotification]:
    statement = select(InAppNotification).order_by(InAppNotification.created_at.desc())  # type: ignore[attr-defined]
    if unread_only:
        statement = statement.where(InAppNotification.read.is_(False))  # type: ignore[attr-defined]
    return list(session.exec(statement.limit(limit)).all())


def unread_inapp_count(session: Session) -> int:
    rows = session.exec(
        select(InAppNotification).where(InAppNotification.read.is_(False))  # type: ignore[attr-defined]
    ).all()
    return len(list(rows))
