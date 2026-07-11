"""Connection persistence and test orchestration."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from sqlmodel import Session, select

from plextraktbox.clients import letterboxd_client, plex_client, tmdb_client, trakt_client
from plextraktbox.clients.base import ConnectionTestResult
from plextraktbox.config import get_settings
from plextraktbox.logging_setup import get_logger
from plextraktbox.models.connection import Connection, ConnectionStatus, Service
from plextraktbox.security import decrypt_secret, encrypt_secret

log = get_logger(__name__)

ALL_SERVICES = (
    Service.PLEX,
    Service.TRAKT,
    Service.LETTERBOXD,
    Service.TMDB,
)


def get_connection(session: Session, service: Service) -> Connection | None:
    return session.exec(select(Connection).where(Connection.service == service)).first()


def list_connections(session: Session) -> dict[Service, Connection | None]:
    rows = session.exec(select(Connection)).all()
    by_service = {row.service: row for row in rows}
    return {service: by_service.get(service) for service in ALL_SERVICES}


def needs_connections(session: Session) -> bool:
    for service in ALL_SERVICES:
        connection = get_connection(session, service)
        if connection is None or connection.status != ConnectionStatus.OK:
            return True
    return False


def _load_secrets(connection: Connection) -> dict[str, Any]:
    if not connection.secret_enc:
        return {}
    plaintext = decrypt_secret(connection.secret_enc)
    data = json.loads(plaintext)
    return data if isinstance(data, dict) else {}


def _save_connection(
    session: Session,
    *,
    service: Service,
    config: dict[str, Any],
    secrets: dict[str, Any],
    status: ConnectionStatus,
    token_expires_at: datetime | None = None,
) -> Connection:
    connection = get_connection(session, service)
    if connection is None:
        connection = Connection(service=service)
        session.add(connection)

    connection.config_json = json.dumps(config)
    connection.secret_enc = encrypt_secret(json.dumps(secrets))
    connection.status = status
    connection.token_expires_at = token_expires_at
    session.commit()
    session.refresh(connection)
    return connection


def save_plex(session: Session, *, url: str, token: str, test: bool = True) -> Connection:
    if test:
        result = plex_client.test_connection(url, token)
        if not result.ok:
            raise ValueError(result.message)

    return _save_connection(
        session,
        service=Service.PLEX,
        config={"url": url.rstrip("/")},
        secrets={"token": token},
        status=ConnectionStatus.OK,
    )


def save_plex_from_pin(
    session: Session,
    *,
    account_token: str,
    client_identifier: str,
) -> Connection:
    server, result = plex_client.find_connectable_server(account_token, client_identifier)
    verified = server is not None and result is not None and result.ok
    if not verified:
        discovered = plex_client.discover_servers(account_token, client_identifier)
        fallback = plex_client.pick_best_server(discovered)
        if fallback is None:
            if result is not None:
                raise ValueError(
                    result.message
                    + " — try again, or save your Plex server URL manually if the container cannot reach it."
                )
            raise ValueError("No Plex Media Server found on your Plex account")
        server = fallback
        log.warning(
            "connection.plex.pin.server_unverified",
            url=server.url,
            friendly_name=server.friendly_name,
            machine_id=server.machine_id,
            last_error=result.message if result is not None else None,
        )

    if server is None:
        raise ValueError("No Plex Media Server found on your Plex account")

    config: dict[str, Any] = {"url": server.url.rstrip("/")}
    if verified and result is not None and result.details:
        if friendly_name := result.details.get("friendly_name"):
            config["friendly_name"] = friendly_name
        if machine_id := result.details.get("machine_id"):
            config["machine_id"] = machine_id
    else:
        if server.friendly_name:
            config["friendly_name"] = server.friendly_name
        if server.machine_id:
            config["machine_id"] = server.machine_id

    connection = _save_connection(
        session,
        service=Service.PLEX,
        config=config,
        secrets={"token": server.token},
        status=ConnectionStatus.OK,
    )
    log.info(
        "connection.plex.saved",
        via="pin",
        url=config.get("url"),
        friendly_name=config.get("friendly_name"),
        machine_id=config.get("machine_id"),
    )
    return connection


def resolve_letterboxd_password(session: Session, password: str | None) -> str:
    if password is not None:
        return password
    connection = get_connection(session, Service.LETTERBOXD)
    if connection is None or not connection.secret_enc:
        raise ValueError("Password is required")
    saved = _load_secrets(connection).get("password", "")
    if not saved:
        raise ValueError("Password is required")
    return saved


def save_letterboxd(
    session: Session,
    *,
    username: str,
    password: str | None,
    test: bool = True,
) -> Connection:
    resolved_password = resolve_letterboxd_password(session, password)
    if test:
        result = letterboxd_client.test_connection(username, resolved_password)
        if not result.ok:
            raise ValueError(result.message)

    return _save_connection(
        session,
        service=Service.LETTERBOXD,
        config={"username": username},
        secrets={"password": resolved_password},
        status=ConnectionStatus.OK,
    )


def save_tmdb(session: Session, *, api_key: str, test: bool = True) -> Connection:
    if test:
        result = tmdb_client.test_connection(api_key)
        if not result.ok:
            raise ValueError(result.message)

    return _save_connection(
        session,
        service=Service.TMDB,
        config={},
        secrets={"api_key": api_key},
        status=ConnectionStatus.OK,
    )


def save_trakt_tokens(
    session: Session,
    *,
    access_token: str,
    refresh_token: str,
    expires_at: datetime | None,
    test: bool = True,
) -> Connection:
    client_id, client_secret = get_settings().require_trakt_credentials()
    if test:
        result, refreshed = trakt_client.test_connection(
            client_id,
            client_secret,
            access_token,
            refresh_token,
            token_expires_at=expires_at,
        )
        if not result.ok:
            raise ValueError(result.message)
        if refreshed is not None:
            access_token = refreshed.access_token
            refresh_token = refreshed.refresh_token
            expires_at = refreshed.expires_at

    return _save_connection(
        session,
        service=Service.TRAKT,
        config={},
        secrets={
            "access_token": access_token,
            "refresh_token": refresh_token,
        },
        status=ConnectionStatus.OK,
        token_expires_at=expires_at,
    )


def clear_all_connections(session: Session) -> None:
    rows = session.exec(select(Connection)).all()
    for row in rows:
        session.delete(row)
    session.commit()


def clear_connection(session: Session, service: Service) -> None:
    connection = get_connection(session, service)
    if connection is None:
        return
    session.delete(connection)
    session.commit()


def mark_trakt_needs_reauth(session: Session) -> None:
    connection = get_connection(session, Service.TRAKT)
    if connection is None:
        return
    connection.status = ConnectionStatus.NEEDS_REAUTH
    session.add(connection)
    session.commit()


def test_saved_connection(session: Session, service: Service) -> ConnectionTestResult:
    connection = get_connection(session, service)
    if connection is None or not connection.secret_enc:
        return ConnectionTestResult(ok=False, message="Connection not configured")

    config = connection.public_config()
    secrets = _load_secrets(connection)

    if service == Service.PLEX:
        return plex_client.test_connection(config.get("url", ""), secrets.get("token", ""))

    if service == Service.LETTERBOXD:
        return letterboxd_client.test_connection(
            config.get("username", ""),
            secrets.get("password", ""),
        )

    if service == Service.TMDB:
        return tmdb_client.test_connection(secrets.get("api_key", ""))

    if service == Service.TRAKT:
        try:
            client_id, client_secret = get_settings().require_trakt_credentials()
        except ValueError as exc:
            return ConnectionTestResult(ok=False, message=str(exc))

        result, refreshed = trakt_client.test_connection(
            client_id,
            client_secret,
            secrets.get("access_token", ""),
            secrets.get("refresh_token", ""),
            token_expires_at=connection.token_expires_at,
        )
        if refreshed is not None:
            save_trakt_tokens(
                session,
                access_token=refreshed.access_token,
                refresh_token=refreshed.refresh_token,
                expires_at=refreshed.expires_at,
                test=False,
            )
        elif not result.ok and "re-authorize" in result.message.lower():
            mark_trakt_needs_reauth(session)
        elif result.ok and connection.status == ConnectionStatus.NEEDS_REAUTH:
            connection.status = ConnectionStatus.OK
            session.add(connection)
            session.commit()
        return result

    return ConnectionTestResult(ok=False, message=f"Unknown service: {service}")
