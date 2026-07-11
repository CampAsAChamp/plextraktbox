"""Shared types for service connection tests."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ConnectionTestResult:
    ok: bool
    message: str
    details: dict[str, str] | None = None
