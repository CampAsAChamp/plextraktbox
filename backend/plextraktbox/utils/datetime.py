"""UTC datetime helpers for API serialization."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated

from pydantic import PlainSerializer


def as_utc_datetime(value: datetime) -> datetime:
    """Treat naive datetimes as UTC (SQLite strips tzinfo on read)."""
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def serialize_utc_datetime(value: datetime) -> str:
    """Serialize a datetime for JSON clients as an explicit UTC instant."""
    return as_utc_datetime(value).isoformat().replace("+00:00", "Z")


UtcDatetime = Annotated[
    datetime,
    PlainSerializer(serialize_utc_datetime, return_type=str, when_used="json"),
]
