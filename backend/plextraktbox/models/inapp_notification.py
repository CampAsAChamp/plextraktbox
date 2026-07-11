"""In-app notification rows (navbar bell)."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from sqlmodel import Field, SQLModel


class InAppLevel(StrEnum):
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


class InAppNotification(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC), index=True)
    level: InAppLevel = Field(default=InAppLevel.INFO)
    title: str
    body: str
    read: bool = Field(default=False, index=True)
    run_id: int | None = Field(default=None, nullable=True, index=True)
