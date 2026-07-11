"""UTC datetime serialization tests."""

from __future__ import annotations

from datetime import UTC, datetime

from plextraktbox.schemas.log import LogEntryItem
from plextraktbox.utils.datetime import as_utc_datetime, serialize_utc_datetime


def test_as_utc_datetime_treats_naive_values_as_utc() -> None:
    naive = datetime(2026, 7, 11, 19, 31, 5, 685000)
    aware = as_utc_datetime(naive)
    assert aware.tzinfo is UTC
    assert aware.hour == 19


def test_serialize_utc_datetime_uses_z_suffix() -> None:
    naive = datetime(2026, 7, 11, 19, 31, 5, 685000)
    assert serialize_utc_datetime(naive) == "2026-07-11T19:31:05.685000Z"


def test_log_entry_item_serializes_ts_with_z_suffix() -> None:
    item = LogEntryItem(
        id=1,
        run_id=2,
        ts=datetime(2026, 7, 11, 19, 31, 5, 685000),
        level="info",
        logger="test",
        message="hello",
        context={},
    )
    assert item.model_dump(mode="json")["ts"] == "2026-07-11T19:31:05.685000Z"
