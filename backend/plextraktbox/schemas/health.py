"""Health check response schema."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"] = "ok"
    version: str
    git_sha: str | None = None
    built_at: str | None = None
    db_writable: bool = True
    scheduler_running: bool = True
    connections: dict[str, str] = Field(default_factory=dict)
