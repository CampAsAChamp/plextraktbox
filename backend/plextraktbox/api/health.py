"""Health check endpoint (unauthenticated)."""

from __future__ import annotations

from fastapi import APIRouter, Request
from sqlalchemy import text
from sqlmodel import Session, select

from plextraktbox import db
from plextraktbox.models.connection import Connection, ConnectionStatus, Service
from plextraktbox.schemas.health import HealthResponse
from plextraktbox.version_info import __version__, built_at, git_sha

router = APIRouter(tags=["health"])


def _db_writable() -> bool:
    try:
        with db.engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            conn.execute(text("PRAGMA user_version"))
            conn.commit()
        return True
    except Exception:
        return False


def _connection_summary() -> dict[str, str]:
    summary = {service.value: ConnectionStatus.UNCONFIGURED.value for service in Service}
    try:
        with Session(db.engine) as session:
            rows = list(session.exec(select(Connection)).all())
    except Exception:
        return summary
    for row in rows:
        summary[row.service.value] = row.status.value
    return summary


@router.get("/health")
def health(request: Request) -> HealthResponse:
    db_ok = _db_writable()
    scheduler = getattr(request.app.state, "scheduler", None)
    scheduler_ok = bool(scheduler is not None and getattr(scheduler, "running", False))
    connections = _connection_summary()
    degraded = (
        (not db_ok)
        or (not scheduler_ok)
        or any(
            status in {ConnectionStatus.NEEDS_REAUTH.value, ConnectionStatus.ERROR.value}
            for status in connections.values()
        )
    )
    return HealthResponse(
        status="degraded" if degraded else "ok",
        version=__version__,
        git_sha=git_sha(),
        built_at=built_at(),
        db_writable=db_ok,
        scheduler_running=scheduler_ok,
        connections=connections,
    )
