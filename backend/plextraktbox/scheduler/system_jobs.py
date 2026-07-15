"""Fixed APScheduler system jobs (connection health + log retention)."""

from __future__ import annotations

from sqlmodel import Session

from plextraktbox import db
from plextraktbox.logging_setup import get_logger
from plextraktbox.models.connection import ConnectionStatus, Service
from plextraktbox.notifications.dispatcher import dispatch_connection_needs_reauth
from plextraktbox.services import connections as conn_svc
from plextraktbox.services.retention import prune_old_runs

log = get_logger(__name__)

CONNECTION_HEALTH_JOB_ID = "system_connection_health"
LOG_RETENTION_JOB_ID = "system_log_retention"
CONNECTION_HEALTH_CRON = "0 */6 * * *"
LOG_RETENTION_CRON = "15 4 * * *"


def run_connection_health_checks() -> None:
    """Probe saved connections and update status; notify on needs_reauth transitions."""
    with Session(db.engine) as session:
        for service in Service:
            connection = conn_svc.get_connection(session, service)
            if connection is None or not connection.secret_enc:
                continue

            previous = connection.status
            result = conn_svc.test_saved_connection(session, service)
            session.refresh(connection)

            if result.ok:
                if connection.status != ConnectionStatus.OK:
                    connection.status = ConnectionStatus.OK
                    session.add(connection)
                    session.commit()
                continue

            message_lower = result.message.lower()
            if "re-authorize" in message_lower or "reauth" in message_lower or "expired" in message_lower:
                new_status = ConnectionStatus.NEEDS_REAUTH
            else:
                new_status = ConnectionStatus.ERROR

            if connection.status != new_status:
                connection.status = new_status
                session.add(connection)
                session.commit()

            if previous != ConnectionStatus.NEEDS_REAUTH and new_status == ConnectionStatus.NEEDS_REAUTH:
                dispatch_connection_needs_reauth(session, service, result.message)

            log.warning(
                "system.connection_health.failed",
                service=service.value,
                status=new_status.value,
                message=result.message,
            )


def run_log_retention() -> None:
    with Session(db.engine) as session:
        prune_old_runs(session)
