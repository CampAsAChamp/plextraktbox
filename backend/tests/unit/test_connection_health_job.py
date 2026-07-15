"""Scheduled connection health job tests."""

from __future__ import annotations

from unittest.mock import patch

from sqlmodel import Session, select

from plextraktbox.clients.base import ConnectionTestResult
from plextraktbox.models.connection import Connection, ConnectionStatus, Service
from plextraktbox.models.inapp_notification import InAppNotification
from plextraktbox.scheduler.system_jobs import run_connection_health_checks
from plextraktbox.security import encrypt_secret


def test_connection_health_notifies_on_needs_reauth_transition(session: Session) -> None:
    connection = Connection(
        service=Service.TRAKT,
        status=ConnectionStatus.OK,
        config_json="{}",
        secret_enc=encrypt_secret('{"access_token":"a","refresh_token":"r"}'),
    )
    session.add(connection)
    session.commit()

    with patch(
        "plextraktbox.services.connections.test_saved_connection",
        return_value=ConnectionTestResult(ok=False, message="Please re-authorize Trakt"),
    ):
        run_connection_health_checks()

    session.refresh(connection)
    assert connection.status == ConnectionStatus.NEEDS_REAUTH
    notes = list(session.exec(select(InAppNotification)).all())
    assert len(notes) == 1
    assert "re-authorization" in notes[0].title.lower() or "trakt" in notes[0].title.lower()


def test_connection_health_no_duplicate_notify(session: Session) -> None:
    connection = Connection(
        service=Service.TRAKT,
        status=ConnectionStatus.NEEDS_REAUTH,
        config_json="{}",
        secret_enc=encrypt_secret('{"access_token":"a","refresh_token":"r"}'),
    )
    session.add(connection)
    session.commit()

    with patch(
        "plextraktbox.services.connections.test_saved_connection",
        return_value=ConnectionTestResult(ok=False, message="Please re-authorize Trakt"),
    ):
        run_connection_health_checks()

    notes = list(session.exec(select(InAppNotification)).all())
    assert notes == []
