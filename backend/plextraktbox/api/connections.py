"""Authenticated connection management endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from plextraktbox.api.deps import CurrentUserDep, SessionDep, require_csrf
from plextraktbox.clients import letterboxd_client, plex_client, tmdb_client, trakt_client
from plextraktbox.config import get_settings
from plextraktbox.models.connection import Service
from plextraktbox.schemas.connection import (
    ConnectionsStatusResponse,
    ConnectionSummary,
    ConnectionTestResponse,
    LetterboxdConnectionRequest,
    PlexConnectionRequest,
    PlexPinPollRequest,
    PlexPinPollResponse,
    PlexPinStartResponse,
    TmdbConnectionRequest,
    TraktDevicePollRequest,
    TraktDevicePollResponse,
    TraktDeviceStartResponse,
)
from plextraktbox.logging_setup import get_logger
from plextraktbox.services import connections as conn_svc

log = get_logger(__name__)

router = APIRouter(prefix="/connections", tags=["connections"])


@router.get("/status", response_model=ConnectionsStatusResponse)
def connections_status(
    _user: CurrentUserDep,
    session: SessionDep,
) -> ConnectionsStatusResponse:
    by_service = conn_svc.list_connections(session)
    summaries = [
        ConnectionSummary.from_connection(by_service[service], service) for service in conn_svc.ALL_SERVICES
    ]
    return ConnectionsStatusResponse(
        needs_connections=conn_svc.needs_connections(session),
        connections=summaries,
    )


@router.get("", response_model=list[ConnectionSummary])
def list_connections(_user: CurrentUserDep, session: SessionDep) -> list[ConnectionSummary]:
    by_service = conn_svc.list_connections(session)
    return [
        ConnectionSummary.from_connection(by_service[service], service) for service in conn_svc.ALL_SERVICES
    ]


@router.post(
    "/plex",
    response_model=ConnectionSummary,
    dependencies=[Depends(require_csrf)],
)
def save_plex(
    body: PlexConnectionRequest,
    _user: CurrentUserDep,
    session: SessionDep,
) -> ConnectionSummary:
    try:
        connection = conn_svc.save_plex(
            session,
            url=str(body.url),
            token=body.token,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return ConnectionSummary.from_connection(connection, Service.PLEX)


@router.post(
    "/plex/pin/start",
    response_model=PlexPinStartResponse,
    dependencies=[Depends(require_csrf)],
)
def plex_pin_start() -> PlexPinStartResponse:
    try:
        client_id = get_settings().plex_client_identifier
        start = plex_client.start_pin_flow(client_id)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not start Plex authorization: {exc}",
        ) from exc
    log.info(
        "connection.plex.pin.start",
        service="plex",
        pin_id=start.pin_id,
        expires_in=start.expires_in,
        poll_interval_s=start.interval,
    )
    return PlexPinStartResponse(
        pin_id=start.pin_id,
        pin_code=start.pin_code,
        auth_url=start.auth_url,
        verification_url=start.verification_url,
        expires_in=start.expires_in,
        interval=start.interval,
    )


@router.post(
    "/plex/pin/poll",
    response_model=PlexPinPollResponse,
    dependencies=[Depends(require_csrf)],
)
def plex_pin_poll(
    body: PlexPinPollRequest,
    _user: CurrentUserDep,
    session: SessionDep,
) -> PlexPinPollResponse:
    try:
        client_id = get_settings().plex_client_identifier
        poll_status, account_token = plex_client.poll_pin_token(
            client_id,
            body.pin_id,
            body.pin_code,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Plex authorization failed: {exc}",
        ) from exc

    if poll_status == "pending" or account_token is None:
        log.info(
            "connection.plex.pin.poll",
            service="plex",
            pin_id=body.pin_id,
            status="pending",
            authorized=False,
        )
        return PlexPinPollResponse(status="pending", connection=None)

    try:
        connection = conn_svc.save_plex_from_pin(
            session,
            account_token=account_token,
            client_identifier=client_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    summary = ConnectionSummary.from_connection(connection, Service.PLEX)
    log.info(
        "connection.plex.pin.poll",
        service="plex",
        pin_id=body.pin_id,
        status="ok",
        authorized=True,
        url=summary.config.get("url"),
        friendly_name=summary.config.get("friendly_name"),
        machine_id=summary.config.get("machine_id"),
    )
    return PlexPinPollResponse(status="ok", connection=summary)


@router.post(
    "/letterboxd",
    response_model=ConnectionSummary,
    dependencies=[Depends(require_csrf)],
)
def save_letterboxd(
    body: LetterboxdConnectionRequest,
    _user: CurrentUserDep,
    session: SessionDep,
) -> ConnectionSummary:
    try:
        connection = conn_svc.save_letterboxd(
            session,
            username=body.username,
            password=body.password,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return ConnectionSummary.from_connection(connection, Service.LETTERBOXD)


@router.post(
    "/tmdb",
    response_model=ConnectionSummary,
    dependencies=[Depends(require_csrf)],
)
def save_tmdb(
    body: TmdbConnectionRequest,
    _user: CurrentUserDep,
    session: SessionDep,
) -> ConnectionSummary:
    try:
        connection = conn_svc.save_tmdb(session, api_key=body.api_key)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return ConnectionSummary.from_connection(connection, Service.TMDB)


@router.post(
    "/plex/test",
    response_model=ConnectionTestResponse,
    dependencies=[Depends(require_csrf)],
)
def test_plex(body: PlexConnectionRequest) -> ConnectionTestResponse:
    result = plex_client.test_connection(str(body.url), body.token)
    return ConnectionTestResponse(ok=result.ok, message=result.message, details=result.details)


@router.post(
    "/letterboxd/test",
    response_model=ConnectionTestResponse,
    dependencies=[Depends(require_csrf)],
)
def test_letterboxd(
    body: LetterboxdConnectionRequest,
    _user: CurrentUserDep,
    session: SessionDep,
) -> ConnectionTestResponse:
    try:
        password = conn_svc.resolve_letterboxd_password(session, body.password)
    except ValueError as exc:
        return ConnectionTestResponse(ok=False, message=str(exc))
    result = letterboxd_client.test_connection(body.username, password)
    return ConnectionTestResponse(ok=result.ok, message=result.message, details=result.details)


@router.post(
    "/tmdb/test",
    response_model=ConnectionTestResponse,
    dependencies=[Depends(require_csrf)],
)
def test_tmdb(body: TmdbConnectionRequest) -> ConnectionTestResponse:
    result = tmdb_client.test_connection(body.api_key)
    return ConnectionTestResponse(ok=result.ok, message=result.message, details=result.details)


@router.post(
    "/trakt/device/start",
    response_model=TraktDeviceStartResponse,
    dependencies=[Depends(require_csrf)],
)
def trakt_device_start() -> TraktDeviceStartResponse:
    try:
        client_id, _ = get_settings().require_trakt_credentials()
        start = trakt_client.start_device_flow(client_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not start Trakt authorization: {exc}",
        ) from exc
    log.info(
        "connection.trakt.device.start",
        service="trakt",
        user_code=start.user_code,
        expires_in=start.expires_in,
        poll_interval_s=start.interval,
    )
    return TraktDeviceStartResponse(
        user_code=start.user_code,
        device_code=start.device_code,
        verification_url=start.verification_url,
        expires_in=start.expires_in,
        interval=start.interval,
    )


@router.post(
    "/trakt/device/poll",
    response_model=TraktDevicePollResponse,
    dependencies=[Depends(require_csrf)],
)
def trakt_device_poll(
    body: TraktDevicePollRequest,
    _user: CurrentUserDep,
    session: SessionDep,
) -> TraktDevicePollResponse:
    try:
        client_id, client_secret = get_settings().require_trakt_credentials()
        poll_status, tokens = trakt_client.poll_device_token(
            client_id,
            client_secret,
            body.device_code,
        )
    except ValueError as exc:
        detail = str(exc)
        if "not configured" in detail.lower():
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=detail) from exc
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Trakt authorization failed: {exc}",
        ) from exc

    if poll_status == "pending" or tokens is None:
        log.info(
            "connection.trakt.device.poll",
            service="trakt",
            status="pending",
            authorized=False,
        )
        return TraktDevicePollResponse(status="pending", connection=None)

    try:
        connection = conn_svc.save_trakt_tokens(
            session,
            access_token=tokens.access_token,
            refresh_token=tokens.refresh_token,
            expires_at=tokens.expires_at,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    summary = ConnectionSummary.from_connection(connection, Service.TRAKT)
    log.info(
        "connection.trakt.device.poll",
        service="trakt",
        status="ok",
        authorized=True,
        connection_status=summary.status,
    )
    return TraktDevicePollResponse(status="ok", connection=summary)


@router.delete(
    "/{service}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_csrf)],
)
def clear_connection(
    service: Service,
    _user: CurrentUserDep,
    session: SessionDep,
) -> None:
    conn_svc.clear_connection(session, service)


@router.delete(
    "",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_csrf)],
)
def clear_connections(
    _user: CurrentUserDep,
    session: SessionDep,
) -> None:
    conn_svc.clear_all_connections(session)


@router.post(
    "/{service}/test",
    response_model=ConnectionTestResponse,
    dependencies=[Depends(require_csrf)],
)
def test_saved_connection(
    service: Service,
    _user: CurrentUserDep,
    session: SessionDep,
) -> ConnectionTestResponse:
    result = conn_svc.test_saved_connection(session, service)
    return ConnectionTestResponse(ok=result.ok, message=result.message, details=result.details)
