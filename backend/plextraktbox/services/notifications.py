"""Notification config persistence helpers."""

from __future__ import annotations

from sqlmodel import Session, select

from plextraktbox.models.job import Job
from plextraktbox.models.notification_config import (
    NotificationChannel,
    NotificationConfig,
    NotificationScope,
)
from plextraktbox.schemas.notification import (
    NotificationConfigCreateRequest,
    NotificationConfigUpdateRequest,
)
from plextraktbox.security import encrypt_secret


def list_configs(
    session: Session,
    *,
    scope: NotificationScope | None = None,
    job_id: int | None = None,
) -> list[NotificationConfig]:
    statement = select(NotificationConfig).order_by(NotificationConfig.id)  # type: ignore[arg-type]
    if scope is not None:
        statement = statement.where(NotificationConfig.scope == scope)
    if job_id is not None:
        statement = statement.where(NotificationConfig.job_id == job_id)
    return list(session.exec(statement).all())


def get_config(session: Session, config_id: int) -> NotificationConfig | None:
    return session.get(NotificationConfig, config_id)


def _find_existing(
    session: Session,
    *,
    channel: NotificationChannel,
    scope: NotificationScope,
    job_id: int | None,
) -> NotificationConfig | None:
    statement = select(NotificationConfig).where(
        NotificationConfig.channel == channel,
        NotificationConfig.scope == scope,
    )
    if scope == NotificationScope.JOB:
        statement = statement.where(NotificationConfig.job_id == job_id)
    else:
        statement = statement.where(NotificationConfig.job_id.is_(None))  # type: ignore[union-attr]
    return session.exec(statement).first()


def create_config(session: Session, body: NotificationConfigCreateRequest) -> NotificationConfig:
    if body.scope == NotificationScope.JOB:
        if body.job_id is None:
            raise ValueError("job_id is required for job-scoped notifications")
        job = session.get(Job, body.job_id)
        if job is None:
            raise ValueError("Job not found")
    elif body.job_id is not None:
        raise ValueError("job_id must be omitted for global notifications")

    existing = _find_existing(
        session,
        channel=body.channel,
        scope=body.scope,
        job_id=body.job_id,
    )
    if existing is not None:
        raise ValueError("A notification config already exists for this channel and scope")

    config = NotificationConfig(
        channel=body.channel,
        enabled=body.enabled,
        on_success=body.on_success,
        on_failure=body.on_failure,
        scope=body.scope,
        job_id=body.job_id,
    )
    _apply_channel_input(config, body)
    session.add(config)
    session.commit()
    session.refresh(config)
    return config


def update_config(
    session: Session,
    config: NotificationConfig,
    body: NotificationConfigUpdateRequest,
) -> NotificationConfig:
    config.enabled = body.enabled
    config.on_success = body.on_success
    config.on_failure = body.on_failure
    if (
        body.discord is not None
        and config.channel == NotificationChannel.DISCORD
        and body.discord.webhook_url
    ):
        config.config_enc = encrypt_secret(body.discord.webhook_url)
    session.add(config)
    session.commit()
    session.refresh(config)
    return config


def delete_config(session: Session, config: NotificationConfig) -> None:
    session.delete(config)
    session.commit()


def _apply_channel_input(config: NotificationConfig, body: NotificationConfigCreateRequest) -> None:
    if config.channel == NotificationChannel.DISCORD:
        if body.discord is None or not body.discord.webhook_url:
            raise ValueError("Discord webhook URL is required")
        config.config_enc = encrypt_secret(body.discord.webhook_url)
        config.config_json = "{}"
        return

    if config.channel == NotificationChannel.INAPP:
        config.config_json = "{}"
        config.config_enc = ""
        return

    raise ValueError(f"Unsupported channel: {config.channel}")
