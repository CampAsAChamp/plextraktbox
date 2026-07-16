"""Shared helpers for SQLite-backed sync caches."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlmodel import Session, SQLModel, select


def get_engine():
    """Lazy DB engine import (avoids circular imports at module load)."""
    from plextraktbox import db

    return db.engine


def clear_all_rows(model: type[SQLModel], session: Session | None = None) -> int:
    """Delete all rows for ``model``. Owns a session when none is passed."""
    owns = session is None
    if owns:
        session = Session(get_engine())
    assert session is not None
    try:
        rows = list(session.exec(select(model)).all())
        count = len(rows)
        for row in rows:
            session.delete(row)
        session.commit()
        return count
    finally:
        if owns:
            session.close()


def is_within_ttl(fetched_at: datetime, *, ttl: timedelta) -> bool:
    """Return True when ``fetched_at`` is still fresh for ``ttl`` (naive = UTC)."""
    aware = fetched_at if fetched_at.tzinfo is not None else fetched_at.replace(tzinfo=UTC)
    return datetime.now(UTC) - aware <= ttl


def ensure_utc(value: datetime) -> datetime:
    """Treat naive datetimes as UTC."""
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
