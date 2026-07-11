"""Persisted sync run log lines."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from sqlmodel import Field, SQLModel


class LogEntry(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    run_id: int = Field(index=True)
    ts: datetime = Field(default_factory=lambda: datetime.now(UTC), index=True)
    level: str = Field(default="info", max_length=16)
    logger: str = Field(default="", max_length=255)
    message: str = Field(default="")
    context_json: str = Field(default="{}")

    def context(self) -> dict[str, Any]:
        try:
            raw = json.loads(self.context_json)
        except json.JSONDecodeError:
            return {}
        return raw if isinstance(raw, dict) else {}

    def set_context(self, context: dict[str, Any]) -> None:
        self.context_json = json.dumps(context)
