"""Run log query helpers."""

from __future__ import annotations

from collections.abc import Iterator

from sqlmodel import Session, col, select

from plextraktbox.models.log_entry import LogEntry

# Page size when streaming an entire run for export.
_EXPORT_PAGE_SIZE = 2000


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


def iter_all_log_entries(session: Session, run_id: int) -> Iterator[LogEntry]:
    """Yield every log entry for a run in id order (paginated under the hood)."""
    after_id = 0
    while True:
        page = list_log_entries(
            session,
            run_id,
            after_id=after_id,
            limit=_EXPORT_PAGE_SIZE,
        )
        if not page:
            return
        for entry in page:
            yield entry
            if entry.id is not None:
                after_id = entry.id
        if len(page) < _EXPORT_PAGE_SIZE:
            return
