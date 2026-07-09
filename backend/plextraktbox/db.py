"""Database engine and session management."""

from __future__ import annotations

from collections.abc import Iterator

from sqlmodel import Session, SQLModel, create_engine

from plextraktbox.config import get_settings

_settings = get_settings()

# check_same_thread=False: SQLite is accessed from FastAPI request threads and the
# APScheduler executor thread. Writes are serialized by SQLite's file lock.
engine = create_engine(
    _settings.database_url,
    echo=False,
    connect_args={"check_same_thread": False},
)


def init_db() -> None:
    """Create tables for any models not yet managed by Alembic.

    Alembic owns schema evolution in production; this is a convenience for tests
    and first boot where migrations may not have run yet.
    """
    # Import models so they register with SQLModel.metadata before create_all.
    import plextraktbox.models  # noqa: F401

    SQLModel.metadata.create_all(engine)


def get_session() -> Iterator[Session]:
    """FastAPI dependency that yields a session and closes it afterwards."""
    with Session(engine) as session:
        yield session
