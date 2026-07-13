"""Pre-flight validation tests."""

from __future__ import annotations

import pytest
from sqlmodel import Session

from plextraktbox.models.connection import Connection, ConnectionStatus, Service
from plextraktbox.models.job import Job, SourcePair
from plextraktbox.security import encrypt_secret
from plextraktbox.services.preflight import validate_job_connections
from plextraktbox.sync.plans import DataType


def _save_ok(session: Session, service: Service) -> None:
    session.add(
        Connection(
            service=service,
            status=ConnectionStatus.OK,
            config_json="{}",
            secret_enc=encrypt_secret('{"token":"x"}'),
        )
    )
    session.commit()


def test_preflight_rejects_missing_connection(session: Session) -> None:
    job = Job(
        name="plex-trakt",
        source_pair=SourcePair.PLEX_TRAKT,
        data_types_json=Job.dump_data_types({DataType.WATCHLIST}),
    )
    session.add(job)
    session.commit()

    with pytest.raises(ValueError, match="Connections not configured"):
        validate_job_connections(session, job)


def test_preflight_rejects_non_ok_connection(session: Session) -> None:
    session.add(
        Connection(
            service=Service.PLEX,
            status=ConnectionStatus.NEEDS_REAUTH,
            config_json='{"url":"http://plex"}',
            secret_enc=encrypt_secret('{"token":"x"}'),
        )
    )
    session.add(
        Connection(
            service=Service.TRAKT,
            status=ConnectionStatus.OK,
            config_json="{}",
            secret_enc=encrypt_secret('{"access_token":"a","refresh_token":"b"}'),
        )
    )
    session.commit()

    job = Job(
        name="plex-trakt",
        source_pair=SourcePair.PLEX_TRAKT,
        data_types_json=Job.dump_data_types({DataType.WATCHLIST}),
    )
    session.add(job)
    session.commit()

    with pytest.raises(ValueError, match="Connections need attention"):
        validate_job_connections(session, job)


def test_preflight_requires_tmdb_for_letterboxd_jobs(session: Session) -> None:
    for service in (Service.LETTERBOXD, Service.PLEX):
        _save_ok(session, service)
    job = Job(
        name="lb-plex",
        source_pair=SourcePair.LETTERBOXD_PLEX,
        data_types_json=Job.dump_data_types({DataType.RATINGS}),
    )
    session.add(job)
    session.commit()

    with pytest.raises(ValueError, match="tmdb"):
        validate_job_connections(session, job)
