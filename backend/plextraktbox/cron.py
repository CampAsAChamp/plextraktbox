"""Cron expression validation and next-fire helpers shared by API and scheduler."""

from __future__ import annotations

from datetime import UTC, datetime

from apscheduler.triggers.cron import CronTrigger


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


def compute_next_run_times(
    cron: str,
    *,
    count: int = 5,
    after: datetime | None = None,
) -> list[datetime]:
    """Return the next ``count`` UTC fire times for a 5-field cron expression."""
    if count < 1:
        raise ValueError("count must be at least 1")
    normalized = validate_cron_expression(cron)
    trigger = CronTrigger.from_crontab(normalized, timezone="UTC")
    start = after if after is not None else datetime.now(UTC)
    start = start.replace(tzinfo=UTC) if start.tzinfo is None else start.astimezone(UTC)

    times: list[datetime] = []
    previous: datetime | None = None
    for _ in range(count):
        nxt = trigger.get_next_fire_time(previous, previous or start)
        if nxt is None:
            break
        times.append(nxt)
        previous = nxt
    return times
