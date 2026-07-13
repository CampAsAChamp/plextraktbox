"""Health check response schema."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    version: str
    git_sha: str | None = None
    built_at: str | None = None
