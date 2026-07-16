"""Authenticated connection management endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, status

from plextraktbox.api.deps import CurrentUserDep, SessionDep, require_csrf
from plextraktbox.config import get_settings
from plextraktbox.models.connection import Service
from plextraktbox.schemas.connection import (
    ConnectionsStatusResponse,
    ConnectionSummary,
    ConnectionTestResponse,
    LetterboxdConnectionRequest,
    LetterboxdConnectionTestRequest,
    PlexConnectionRequest,
    PlexConnectionTestRequest,
    PlexLibrariesResponse,
    PlexLibrariesUpdateRequest,
    PlexLibraryInfo,
    PlexPinPollRequest,
    PlexPinPollResponse,
    PlexPinStartResponse,
    TmdbConnectionRequest,
    TmdbConnectionTestRequest,
    TraktDevicePollRequest,
    TraktDevicePollResponse,
    TraktDeviceStartResponse,
    TraktTokensRequest,
)
from plextraktbox.services import connections as conn_svc

router = APIRouter(prefix="/connections", tags=["connections"])


def _value_error_to_http(exc: ValueError, *, trakt_not_configured_503: bool = False) -> HTTPException:
    detail = str(exc)
    if trakt_not_configured_503 and "not configured" in detail.lower():
        return HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=detail)
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


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
        raise _value_error_to_http(exc) from exc
    return ConnectionSummary.from_connection(connection, Service.PLEX)


@router.post(
    "/plex/pin/start",
    response_model=PlexPinStartResponse,
    dependencies=[Depends(require_csrf)],
)
def plex_pin_start() -> PlexPinStartResponse:
    try:
        start = conn_svc.start_plex_pin()
    except ValueError as exc:
        raise _value_error_to_http(exc) from exc
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
        result = conn_svc.poll_plex_pin(session, pin_id=body.pin_id, pin_code=body.pin_code)
    except ValueError as exc:
        raise _value_error_to_http(exc) from exc

    if result.status == "pending":
        return PlexPinPollResponse(status="pending", connection=None)

    summary = ConnectionSummary.from_connection(result.connection, Service.PLEX)
    return PlexPinPollResponse(status="ok", connection=summary)


@router.get(
    "/plex/libraries",
    response_model=PlexLibrariesResponse,
)
def list_plex_libraries(_user: CurrentUserDep, session: SessionDep) -> PlexLibrariesResponse:
    try:
        libraries = conn_svc.list_plex_libraries(session)
    except ValueError as exc:
        raise _value_error_to_http(exc) from exc

    connection = conn_svc.get_connection(session, Service.PLEX)
    config = connection.public_config() if connection else {}
    selected: list[str] = []
    raw = config.get("libraries") or []
    if isinstance(raw, list):
        for entry in raw:
            if isinstance(entry, dict) and entry.get("id") is not None:
                selected.append(str(entry["id"]))
    return PlexLibrariesResponse(
        libraries=[PlexLibraryInfo(**entry) for entry in libraries],
        selected_ids=selected,
    )


@router.put(
    "/plex/libraries",
    response_model=ConnectionSummary,
    dependencies=[Depends(require_csrf)],
)
def update_plex_libraries(
    body: PlexLibrariesUpdateRequest,
    _user: CurrentUserDep,
    session: SessionDep,
) -> ConnectionSummary:
    try:
        connection = conn_svc.update_plex_libraries(session, body.library_ids)
    except ValueError as exc:
        raise _value_error_to_http(exc) from exc
    return ConnectionSummary.from_connection(connection, Service.PLEX)


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
        raise _value_error_to_http(exc) from exc
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
        raise _value_error_to_http(exc) from exc
    return ConnectionSummary.from_connection(connection, Service.TMDB)


@router.post(
    "/plex/test",
    response_model=ConnectionTestResponse,
    dependencies=[Depends(require_csrf)],
)
def test_plex(
    _user: CurrentUserDep,
    session: SessionDep,
    body: Annotated[PlexConnectionTestRequest, Body()] = PlexConnectionTestRequest(),
) -> ConnectionTestResponse:
    result = conn_svc.test_plex_draft_or_saved(
        session,
        url=str(body.url) if body.url is not None else None,
        token=body.token,
    )
    return ConnectionTestResponse(ok=result.ok, message=result.message, details=result.details)


@router.post(
    "/letterboxd/test",
    response_model=ConnectionTestResponse,
    dependencies=[Depends(require_csrf)],
)
def test_letterboxd(
    _user: CurrentUserDep,
    session: SessionDep,
    body: Annotated[LetterboxdConnectionTestRequest, Body()] = LetterboxdConnectionTestRequest(),
) -> ConnectionTestResponse:
    result = conn_svc.test_letterboxd_draft_or_saved(
        session,
        username=body.username,
        password=body.password,
    )
    return ConnectionTestResponse(ok=result.ok, message=result.message, details=result.details)


@router.post(
    "/tmdb/test",
    response_model=ConnectionTestResponse,
    dependencies=[Depends(require_csrf)],
)
def test_tmdb(
    _user: CurrentUserDep,
    session: SessionDep,
    body: Annotated[TmdbConnectionTestRequest, Body()] = TmdbConnectionTestRequest(),
) -> ConnectionTestResponse:
    result = conn_svc.test_tmdb_draft_or_saved(session, api_key=body.api_key)
    return ConnectionTestResponse(ok=result.ok, message=result.message, details=result.details)


@router.post(
    "/trakt/tokens",
    response_model=ConnectionSummary,
    dependencies=[Depends(require_csrf)],
)
def save_trakt_tokens_dev(
    body: TraktTokensRequest,
    _user: CurrentUserDep,
    session: SessionDep,
) -> ConnectionSummary:
    """Import Trakt tokens from .env during local bootstrap (ENV=local only)."""
    if get_settings().env != "local":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not found",
        )
    try:
        connection = conn_svc.save_trakt_tokens(
            session,
            access_token=body.access_token,
            refresh_token=body.refresh_token,
            expires_at=None,
        )
    except ValueError as exc:
        raise _value_error_to_http(exc) from exc
    return ConnectionSummary.from_connection(connection, Service.TRAKT)


@router.post(
    "/trakt/device/start",
    response_model=TraktDeviceStartResponse,
    dependencies=[Depends(require_csrf)],
)
def trakt_device_start() -> TraktDeviceStartResponse:
    try:
        start = conn_svc.start_trakt_device()
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
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
        result = conn_svc.poll_trakt_device(session, device_code=body.device_code)
    except ValueError as exc:
        raise _value_error_to_http(exc, trakt_not_configured_503=True) from exc

    if result.status == "pending":
        return TraktDevicePollResponse(status="pending", connection=None)

    summary = ConnectionSummary.from_connection(result.connection, Service.TRAKT)
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
