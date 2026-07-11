"""Cron expression validation shared by API schemas and the scheduler."""

from __future__ import annotations

from apscheduler.triggers.cron import CronTrigger  # type: ignore[import-untyped]


def validate_cron_expression(cron: str) -> str:
    """Return a normalized cron string or raise ValueError."""
    normalized = cron.strip()
    if not normalized:
        raise ValueError("Cron expression is required")
    try:
        CronTrigger.from_crontab(normalized, timezone="UTC")
    except ValueError as exc:
        raise ValueError(f"Invalid cron expression: {exc}") from exc
    return normalized
