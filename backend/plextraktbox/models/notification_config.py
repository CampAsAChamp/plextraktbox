"""Notification channel configuration (Discord, in-app)."""

from __future__ import annotations

import json
from enum import StrEnum
from typing import Any

from sqlmodel import Field, SQLModel


class NotificationChannel(StrEnum):
    DISCORD = "discord"
    INAPP = "inapp"


class NotificationScope(StrEnum):
    GLOBAL = "global"
    JOB = "job"


class NotificationConfig(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    channel: NotificationChannel = Field(index=True)
    enabled: bool = Field(default=True)
    on_success: bool = Field(default=True)
    on_failure: bool = Field(default=True)
    scope: NotificationScope = Field(default=NotificationScope.GLOBAL, index=True)
    job_id: int | None = Field(default=None, nullable=True, index=True)
    config_enc: str = Field(default="")
    config_json: str = Field(default="{}")

    def public_config(self) -> dict[str, Any]:
        try:
            data = json.loads(self.config_json)
        except json.JSONDecodeError:
            return {}
        return data if isinstance(data, dict) else {}

    def has_secret(self) -> bool:
        return bool(self.config_enc)
