"""Cron expression validation tests."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import patch

import pytest

from plextraktbox.cron import (
    compute_next_run_times,
    resolve_cron_timezone,
    validate_cron_expression,
    validate_cron_timezone,
)


def test_validate_cron_expression_accepts_valid_expressions() -> None:
    assert validate_cron_expression("0 3 * * *") == "0 3 * * *"
    assert validate_cron_expression("  * * * * *  ") == "* * * * *"


@pytest.mark.parametrize(
    "expression",
    ["", "   ", "invalid", "0 3 * *", "99 99 99 99 99"],
)
def test_validate_cron_expression_rejects_invalid_expressions(expression: str) -> None:
    with pytest.raises(ValueError, match="Invalid cron expression|Cron expression is required"):
        validate_cron_expression(expression)


def test_validate_cron_timezone() -> None:
    assert validate_cron_timezone("utc") == "UTC"
    assert validate_cron_timezone("local") == "local"
    assert validate_cron_timezone("America/Los_Angeles") == "America/Los_Angeles"
    with pytest.raises(ValueError, match="Unknown timezone"):
        validate_cron_timezone("Not/A_Zone")


def test_resolve_cron_timezone_local_uses_device_zone() -> None:
    assert resolve_cron_timezone("local", local_zone="America/Chicago") == "America/Chicago"
    with patch("plextraktbox.cron.get_localzone_name", return_value="Europe/Berlin"):
        assert resolve_cron_timezone("local") == "Europe/Berlin"


def test_compute_next_run_times_daily() -> None:
    after = datetime(2026, 7, 14, 12, 0, 0, tzinfo=UTC)
    times = compute_next_run_times("0 3 * * *", count=5, after=after)
    assert times == [
        datetime(2026, 7, 15, 3, 0, tzinfo=UTC),
        datetime(2026, 7, 16, 3, 0, tzinfo=UTC),
        datetime(2026, 7, 17, 3, 0, tzinfo=UTC),
        datetime(2026, 7, 18, 3, 0, tzinfo=UTC),
        datetime(2026, 7, 19, 3, 0, tzinfo=UTC),
    ]


def test_compute_next_run_times_in_local_timezone() -> None:
    # 03:00 America/Los_Angeles on 2026-07-15 is 10:00 UTC (PDT, UTC-7).
    after = datetime(2026, 7, 14, 12, 0, 0, tzinfo=UTC)
    times = compute_next_run_times(
        "0 3 * * *",
        count=1,
        after=after,
        timezone="America/Los_Angeles",
    )
    assert times == [datetime(2026, 7, 15, 10, 0, tzinfo=UTC)]


def test_compute_next_run_times_weekly_monday() -> None:
    # APScheduler crontab weekday 0 = Monday
    after = datetime(2026, 7, 14, 12, 0, 0, tzinfo=UTC)  # Tuesday
    times = compute_next_run_times("0 3 * * 0", count=2, after=after)
    assert times == [
        datetime(2026, 7, 20, 3, 0, tzinfo=UTC),
        datetime(2026, 7, 27, 3, 0, tzinfo=UTC),
    ]


def test_compute_next_run_times_rejects_invalid_cron() -> None:
    with pytest.raises(ValueError, match="Invalid cron expression"):
        compute_next_run_times("not-a-cron", count=5)
