"""Cron expression validation and next-fire helpers shared by API and scheduler."""

from __future__ import annotations

from datetime import UTC, datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from apscheduler.triggers.cron import CronTrigger
from tzlocal import get_localzone_name

DEFAULT_CRON_TIMEZONE = "UTC"


def validate_iana_timezone(timezone: str) -> str:
    """Return a normalized IANA timezone name (not ``local``) or raise ValueError."""
    normalized = timezone.strip()
    if not normalized:
        raise ValueError("Timezone is required")
    if normalized.upper() == "UTC":
        return "UTC"
    if normalized.lower() == "local":
        raise ValueError("Expected an IANA timezone name")
    try:
        ZoneInfo(normalized)
    except (ZoneInfoNotFoundError, KeyError) as exc:
        raise ValueError(f"Unknown timezone: {normalized}") from exc
    return normalized


def validate_cron_timezone(timezone: str) -> str:
    """Return a normalized cron timezone preference or raise ValueError.

    Accepted values: ``UTC``, ``local`` (device timezone snapshot), or an IANA name.
    """
    normalized = timezone.strip()
    if not normalized:
        raise ValueError("Cron timezone is required")
    if normalized.upper() == "UTC":
        return "UTC"
    if normalized.lower() == "local":
        return "local"
    return validate_iana_timezone(normalized)


def resolve_cron_timezone(timezone: str, *, local_zone: str | None = None) -> str:
    """Resolve a cron timezone preference to an IANA name for APScheduler."""
    preference = validate_cron_timezone(timezone)
    if preference == "UTC":
        return "UTC"
    if preference == "local":
        if local_zone and local_zone.strip():
            try:
                return validate_iana_timezone(local_zone)
            except ValueError:
                pass
        name = get_localzone_name()
        if not name:
            return "UTC"
        try:
            return validate_iana_timezone(name)
        except ValueError:
            return "UTC"
    return preference


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
    timezone: str = DEFAULT_CRON_TIMEZONE,
    local_zone: str | None = None,
) -> list[datetime]:
    """Return the next ``count`` fire times (UTC) for a 5-field cron expression."""
    if count < 1:
        raise ValueError("count must be at least 1")
    normalized = validate_cron_expression(cron)
    tz_name = resolve_cron_timezone(timezone, local_zone=local_zone)
    trigger = CronTrigger.from_crontab(normalized, timezone=tz_name)
    start = after if after is not None else datetime.now(UTC)
    start = start.replace(tzinfo=UTC) if start.tzinfo is None else start.astimezone(UTC)

    times: list[datetime] = []
    previous: datetime | None = None
    for _ in range(count):
        nxt = trigger.get_next_fire_time(previous, previous or start)
        if nxt is None:
            break
        if nxt.tzinfo is None:
            times.append(nxt.replace(tzinfo=UTC))
        else:
            times.append(nxt.astimezone(UTC))
        previous = nxt
    return times
