"""Pre-flight validation before starting a sync run."""

from __future__ import annotations

from sqlmodel import Session

from plextraktbox.models.connection import ConnectionStatus, Service
from plextraktbox.models.job import Job, SourcePair
from plextraktbox.services import connections as conn_svc


def _connection_ok(session: Session, service: Service) -> bool:
    connection = conn_svc.get_connection(session, service)
    return connection is not None and connection.status == ConnectionStatus.OK


def _needs_tmdb(session: Session, job: Job) -> bool:
    if "letterboxd" in job.services_for_pair():
        return True
    return job.source_pair == SourcePair.PLEX_TRAKT and _connection_ok(session, Service.LETTERBOXD)


def validate_job_connections(session: Session, job: Job) -> None:
    """Ensure required connections exist and are ``ok`` before creating a JobRun.

    Raises ``ValueError`` with a user-facing message when validation fails.
    """
    required = set(job.services_for_pair())
    if _needs_tmdb(session, job):
        required.add(Service.TMDB.value)

    missing: list[str] = []
    not_ok: list[str] = []

    for name in sorted(required):
        service = Service(name)
        connection = conn_svc.get_connection(session, service)
        if connection is None or not connection.secret_enc:
            missing.append(name)
            continue
        if connection.status != ConnectionStatus.OK:
            not_ok.append(f"{name} ({connection.status.value})")

    if missing:
        raise ValueError(f"Connections not configured: {', '.join(missing)}")
    if not_ok:
        raise ValueError(f"Connections need attention: {', '.join(not_ok)}")

    data_type_errors = job.validate_data_types()
    if data_type_errors:
        raise ValueError("; ".join(data_type_errors))
