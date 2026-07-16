"""SQLite backup validation and restore."""

from __future__ import annotations

import os
import shutil
import sqlite3
from pathlib import Path

from sqlmodel import Session, select

from plextraktbox import db
from plextraktbox.config import get_settings
from plextraktbox.logging_setup import get_logger
from plextraktbox.models.job_run import JobRun, JobRunStatus
from plextraktbox.scheduler import get_scheduler_manager

log = get_logger(__name__)

# Core tables present since early migrations; enough to reject random SQLite files.
REQUIRED_TABLES = frozenset({"user", "setting", "job", "jobrun", "connection"})


class BackupRestoreError(Exception):
    """Invalid backup or restore refused."""

    def __init__(self, message: str, *, status_code: int = 400) -> None:
        super().__init__(message)
        self.status_code = status_code


def validate_sqlite_backup(path: Path) -> None:
    """Ensure ``path`` is a readable SQLite DB with required plextraktbox tables."""
    try:
        conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    except sqlite3.Error as exc:
        raise BackupRestoreError(f"Not a valid SQLite database: {exc}") from exc

    try:
        try:
            rows = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        except sqlite3.Error as exc:
            raise BackupRestoreError(f"Not a valid SQLite database: {exc}") from exc

        tables = {str(row[0]) for row in rows}
        missing = sorted(REQUIRED_TABLES - tables)
        if missing:
            raise BackupRestoreError(
                "Backup is missing required tables: " + ", ".join(missing)
            )

        try:
            conn.execute("SELECT id, username FROM user LIMIT 1").fetchone()
        except sqlite3.Error as exc:
            raise BackupRestoreError(f"Backup user table is unreadable: {exc}") from exc
    finally:
        conn.close()


def _assert_no_running_jobs() -> None:
    with Session(db.engine) as session:
        running = session.exec(
            select(JobRun).where(JobRun.status == JobRunStatus.RUNNING).limit(1)
        ).first()
        if running is not None:
            raise BackupRestoreError(
                "Cannot restore while a sync run is in progress. Wait for it to finish.",
                status_code=409,
            )


def restore_database(upload_path: Path) -> None:
    """Replace the live SQLite file with a validated backup.

    Shuts down the scheduler, disposes the SQLAlchemy pool, atomically replaces
    the DB file, recreates the engine, and restarts the scheduler.
    """
    validate_sqlite_backup(upload_path)
    _assert_no_running_jobs()

    settings = get_settings()
    db_path = settings.db_path
    staging = db_path.with_name(db_path.name + ".restore-staging")
    previous = db_path.with_name(db_path.name + ".pre-restore")

    scheduler = get_scheduler_manager()
    was_running = scheduler.running
    if was_running:
        scheduler.shutdown(wait=True)

    try:
        db.engine.dispose()

        if staging.exists():
            staging.unlink()
        shutil.copy2(upload_path, staging)

        if previous.exists():
            previous.unlink()
        if db_path.exists():
            os.replace(db_path, previous)
        os.replace(staging, db_path)

        db.recreate_engine()
        log.info("backup.restored", db_path=str(db_path))
    except Exception:
        # Best-effort rollback if replace left us without a live DB.
        if not db_path.exists() and previous.exists():
            os.replace(previous, db_path)
        db.recreate_engine()
        raise
    finally:
        if staging.exists():
            staging.unlink(missing_ok=True)
        if was_running:
            scheduler.start()
