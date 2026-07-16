"""Connection persistence and test orchestration."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal

from sqlmodel import Session, select

from plextraktbox.clients import letterboxd_client, plex_client, tmdb_client, trakt_client
from plextraktbox.clients.base import ConnectionTestResult
from plextraktbox.clients.plex_auth import PlexPinStart
from plextraktbox.clients.trakt_client import TraktDeviceStart
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


@dataclass(frozen=True)
class OAuthPollResult:
    status: Literal["pending", "ok"]
    connection: Connection | None = None


def start_plex_pin() -> PlexPinStart:
    try:
        client_id = get_settings().plex_client_identifier
        start = plex_client.start_pin_flow(client_id)
    except Exception as exc:  # noqa: BLE001
        raise ValueError(f"Could not start Plex authorization: {exc}") from exc
    log.info(
        "connection.plex.pin.start",
        service="plex",
        pin_id=start.pin_id,
        expires_in=start.expires_in,
        poll_interval_s=start.interval,
    )
    return start


def poll_plex_pin(session: Session, *, pin_id: int, pin_code: str) -> OAuthPollResult:
    try:
        client_id = get_settings().plex_client_identifier
        poll_status, account_token = plex_client.poll_pin_token(
            client_id,
            pin_id,
            pin_code,
        )
    except ValueError as exc:
        log.warning(
            "connection.plex.pin.poll_failed",
            pin_id=pin_id,
            stage="poll",
            error=str(exc),
        )
        raise
    except Exception as exc:  # noqa: BLE001
        log.warning(
            "connection.plex.pin.poll_failed",
            pin_id=pin_id,
            stage="poll",
            error=str(exc),
        )
        raise ValueError(f"Plex authorization failed: {exc}") from exc

    if poll_status == "pending" or account_token is None:
        log.info(
            "connection.plex.pin.poll",
            service="plex",
            pin_id=pin_id,
            status="pending",
            authorized=False,
        )
        return OAuthPollResult(status="pending")

    try:
        connection = save_plex_from_pin(
            session,
            account_token=account_token,
            client_identifier=client_id,
        )
    except ValueError as exc:
        log.warning(
            "connection.plex.pin.poll_failed",
            pin_id=pin_id,
            stage="save",
            error=str(exc),
        )
        raise

    config = connection.public_config()
    log.info(
        "connection.plex.pin.poll",
        service="plex",
        pin_id=pin_id,
        status="ok",
        authorized=True,
        url=config.get("url"),
        friendly_name=config.get("friendly_name"),
        machine_id=config.get("machine_id"),
    )
    return OAuthPollResult(status="ok", connection=connection)


def start_trakt_device() -> TraktDeviceStart:
    try:
        client_id, _ = get_settings().require_trakt_credentials()
        start = trakt_client.start_device_flow(client_id)
    except ValueError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise ValueError(f"Could not start Trakt authorization: {exc}") from exc
    log.info(
        "connection.trakt.device.start",
        service="trakt",
        user_code=start.user_code,
        expires_in=start.expires_in,
        poll_interval_s=start.interval,
    )
    return start


def poll_trakt_device(session: Session, *, device_code: str) -> OAuthPollResult:
    try:
        client_id, client_secret = get_settings().require_trakt_credentials()
        poll_status, tokens = trakt_client.poll_device_token(
            client_id,
            client_secret,
            device_code,
        )
    except ValueError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise ValueError(f"Trakt authorization failed: {exc}") from exc

    if poll_status == "pending" or tokens is None:
        log.info(
            "connection.trakt.device.poll",
            service="trakt",
            status="pending",
            authorized=False,
        )
        return OAuthPollResult(status="pending")

    connection = save_trakt_tokens(
        session,
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        expires_at=tokens.expires_at,
    )
    log.info(
        "connection.trakt.device.poll",
        service="trakt",
        status="ok",
        authorized=True,
        connection_status=connection.status.value,
    )
    return OAuthPollResult(status="ok", connection=connection)


def test_plex_draft_or_saved(
    session: Session,
    *,
    url: str | None,
    token: str | None,
) -> ConnectionTestResult:
    if url is not None and token:
        return plex_client.test_connection(url, token)
    return test_saved_connection(session, Service.PLEX)


def test_letterboxd_draft_or_saved(
    session: Session,
    *,
    username: str | None,
    password: str | None,
) -> ConnectionTestResult:
    if not username:
        return test_saved_connection(session, Service.LETTERBOXD)
    try:
        resolved_password = resolve_letterboxd_password(session, password)
    except ValueError as exc:
        return ConnectionTestResult(ok=False, message=str(exc))
    return letterboxd_client.test_connection(username, resolved_password)


def test_tmdb_draft_or_saved(
    session: Session,
    *,
    api_key: str | None,
) -> ConnectionTestResult:
    if api_key:
        return tmdb_client.test_connection(api_key)
    return test_saved_connection(session, Service.TMDB)


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


def load_secrets(connection: Connection) -> dict[str, Any]:
    """Return decrypted connection secrets (tokens/passwords)."""
    return _load_secrets(connection)


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
    from plextraktbox.services import letterboxd_export_cache

    resolved_password = resolve_letterboxd_password(session, password)
    if test:
        result = letterboxd_client.test_connection(username, resolved_password)
        if not result.ok:
            raise ValueError(result.message)

    existing = get_connection(session, Service.LETTERBOXD)
    previous_username = ""
    if existing is not None:
        previous_username = str(existing.public_config().get("username", ""))

    connection = _save_connection(
        session,
        service=Service.LETTERBOXD,
        config={"username": username},
        secrets={"password": resolved_password},
        status=ConnectionStatus.OK,
    )
    # Credential changes (or password updates) invalidate the durable export cache.
    if connection.id is not None and (
        existing is None or previous_username != username or password is not None
    ):
        letterboxd_export_cache.invalidate_export_cache(connection.id)
    return connection


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


def ensure_trakt_access_token(session: Session, connection: Connection) -> str:
    """Return a valid Trakt access token, refreshing and persisting when expired."""
    if connection.status != ConnectionStatus.OK:
        raise ValueError("Trakt connection needs re-authorization")

    secrets = _load_secrets(connection)
    access_token = str(secrets.get("access_token", ""))
    refresh_token = str(secrets.get("refresh_token", ""))
    if not access_token or not refresh_token:
        raise ValueError("Trakt connection not configured")

    client_id, client_secret = get_settings().require_trakt_credentials()
    result, refreshed = trakt_client.test_connection(
        client_id,
        client_secret,
        access_token,
        refresh_token,
        token_expires_at=connection.token_expires_at,
    )
    if not result.ok:
        if "re-authorize" in result.message.lower():
            mark_trakt_needs_reauth(session)
        raise ValueError(result.message)

    if refreshed is not None:
        save_trakt_tokens(
            session,
            access_token=refreshed.access_token,
            refresh_token=refreshed.refresh_token,
            expires_at=refreshed.expires_at,
            test=False,
        )
        return refreshed.access_token
    return access_token


def list_plex_libraries(session: Session) -> list[dict[str, str]]:
    connection = get_connection(session, Service.PLEX)
    if connection is None or connection.status != ConnectionStatus.OK:
        raise ValueError("Plex connection not configured")
    config = connection.public_config()
    secrets = _load_secrets(connection)
    libraries = plex_client.list_libraries(
        str(config.get("url", "")),
        str(secrets.get("token", "")),
    )
    return [{"id": lib.id, "title": lib.title, "type": lib.library_type} for lib in libraries]


def update_plex_libraries(session: Session, library_ids: list[str]) -> Connection:
    connection = get_connection(session, Service.PLEX)
    if connection is None:
        raise ValueError("Plex connection not configured")

    config = connection.public_config()
    all_libraries = list_plex_libraries(session)
    selected_ids = {str(value) for value in library_ids}
    selected = [entry for entry in all_libraries if entry["id"] in selected_ids]
    if library_ids and not selected:
        raise ValueError("No matching Plex libraries for selection")

    config["libraries"] = selected
    secrets = _load_secrets(connection)
    return _save_connection(
        session,
        service=Service.PLEX,
        config=config,
        secrets=secrets,
        status=connection.status,
        token_expires_at=connection.token_expires_at,
    )


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
