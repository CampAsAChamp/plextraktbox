"""Run log query helpers."""

from __future__ import annotations

from sqlmodel import Session, col, select

from plextraktbox.models.log_entry import LogEntry


def list_log_entries(
    session: Session,
    run_id: int,
    *,
    after_id: int = 0,
    limit: int = 500,
    level: str | None = None,
    search: str | None = None,
) -> list[LogEntry]:
    stmt = (
        select(LogEntry)
        .where(LogEntry.run_id == run_id, col(LogEntry.id) > after_id)
        .order_by(col(LogEntry.id))
        .limit(limit)
    )
    if level is not None:
        stmt = stmt.where(col(LogEntry.level) == level.lower())
    if search:
        pattern = f"%{search.lower()}%"
        stmt = stmt.where(col(LogEntry.message).ilike(pattern))

    return list(session.exec(stmt).all())
