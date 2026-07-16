"""Notification API schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from plextraktbox.models.inapp_notification import InAppLevel, InAppNotification
from plextraktbox.models.notification_config import (
    NotificationChannel,
    NotificationConfig,
    NotificationScope,
)
from plextraktbox.utils.datetime import UtcDatetime


class DiscordConfigInput(BaseModel):
    webhook_url: str | None = Field(default=None, max_length=2048)


class NotificationConfigCreateRequest(BaseModel):
    channel: NotificationChannel
    enabled: bool = True
    on_success: bool = True
    on_failure: bool = True
    scope: NotificationScope = NotificationScope.GLOBAL
    job_id: int | None = None
    discord: DiscordConfigInput | None = None


class NotificationConfigUpdateRequest(BaseModel):
    enabled: bool = True
    on_success: bool = True
    on_failure: bool = True
    discord: DiscordConfigInput | None = None


class NotificationConfigResponse(BaseModel):
    id: int
    channel: NotificationChannel
    enabled: bool
    on_success: bool
    on_failure: bool
    scope: NotificationScope
    job_id: int | None
    config: dict[str, Any]
    has_secret: bool

    @classmethod
    def from_model(cls, config: NotificationConfig) -> NotificationConfigResponse:
        public = config.public_config()
        if config.channel == NotificationChannel.DISCORD and config.has_secret():
            public = {**public, "webhook_url_configured": True}
        return cls(
            id=config.id or 0,
            channel=config.channel,
            enabled=config.enabled,
            on_success=config.on_success,
            on_failure=config.on_failure,
            scope=config.scope,
            job_id=config.job_id,
            config=public,
            has_secret=config.has_secret(),
        )


class InAppNotificationResponse(BaseModel):
    id: int
    created_at: UtcDatetime
    level: InAppLevel
    title: str
    body: str
    read: bool
    run_id: int | None

    @classmethod
    def from_model(cls, row: InAppNotification) -> InAppNotificationResponse:
        return cls(
            id=row.id or 0,
            created_at=row.created_at,
            level=row.level,
            title=row.title,
            body=row.body,
            read=row.read,
            run_id=row.run_id,
        )


class InAppListResponse(BaseModel):
    items: list[InAppNotificationResponse]
    unread_count: int


class UnreadCountResponse(BaseModel):
    unread_count: int


class NotificationTestResponse(BaseModel):
    ok: bool
    message: str
