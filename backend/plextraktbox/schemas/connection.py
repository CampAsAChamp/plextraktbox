"""Connection request/response DTOs."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, HttpUrl, field_validator

from plextraktbox.models.connection import Connection, ConnectionStatus, Service
from plextraktbox.utils.datetime import UtcDatetime


def _normalize_flaresolverr_url(value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        msg = "flaresolverr_url must be a string"
        raise TypeError(msg)
    stripped = value.strip().rstrip("/")
    return stripped or None


class ConnectionSummary(BaseModel):
    service: Service
    status: ConnectionStatus
    config: dict[str, Any]
    token_expires_at: UtcDatetime | None = None

    @classmethod
    def from_connection(cls, connection: Connection | None, service: Service) -> ConnectionSummary:
        if connection is None:
            return cls(
                service=service,
                status=ConnectionStatus.UNCONFIGURED,
                config={},
            )
        return cls(
            service=connection.service,
            status=connection.status,
            config=connection.public_config(),
            token_expires_at=connection.token_expires_at,
        )


class ConnectionsStatusResponse(BaseModel):
    needs_connections: bool
    connections: list[ConnectionSummary]


class ConnectionTestResponse(BaseModel):
    ok: bool
    message: str
    details: dict[str, str] | None = None


class PlexConnectionRequest(BaseModel):
    url: HttpUrl
    token: str = Field(min_length=1, max_length=512)


class PlexConnectionTestRequest(BaseModel):
    url: HttpUrl | None = None
    token: str | None = Field(default=None, max_length=512)


class LetterboxdConnectionRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str | None = Field(default=None, min_length=1, max_length=128)
    flaresolverr_url: str | None = Field(
        default=None,
        max_length=512,
        description="Optional FlareSolverr base URL for Cloudflare challenges.",
    )
    flaresolverr_timeout_ms: int | None = Field(
        default=None,
        ge=1_000,
        description="Optional FlareSolverr maxTimeout in milliseconds.",
    )

    @field_validator("flaresolverr_url", mode="before")
    @classmethod
    def _normalize_url(cls, value: object) -> str | None:
        return _normalize_flaresolverr_url(value)


class LetterboxdConnectionTestRequest(BaseModel):
    username: str | None = Field(default=None, max_length=64)
    password: str | None = Field(default=None, max_length=128)
    flaresolverr_url: str | None = Field(default=None, max_length=512)
    flaresolverr_timeout_ms: int | None = Field(default=None, ge=1_000)

    @field_validator("flaresolverr_url", mode="before")
    @classmethod
    def _normalize_url(cls, value: object) -> str | None:
        return _normalize_flaresolverr_url(value)


class TmdbConnectionRequest(BaseModel):
    api_key: str = Field(min_length=1, max_length=128)


class TmdbConnectionTestRequest(BaseModel):
    api_key: str | None = Field(default=None, max_length=128)


class TraktDeviceStartResponse(BaseModel):
    user_code: str
    device_code: str
    verification_url: str
    expires_in: int
    interval: int


class TraktDevicePollRequest(BaseModel):
    device_code: str = Field(min_length=1, max_length=256)


class TraktDevicePollResponse(BaseModel):
    status: str
    connection: ConnectionSummary | None = None


class TraktTokensRequest(BaseModel):
    """Dev-only: import Trakt OAuth tokens without repeating device flow."""

    access_token: str = Field(min_length=1, max_length=512)
    refresh_token: str = Field(min_length=1, max_length=512)


class PlexPinStartResponse(BaseModel):
    pin_id: int
    pin_code: str
    auth_url: str
    verification_url: str
    expires_in: int
    interval: int


class PlexPinPollRequest(BaseModel):
    pin_id: int
    pin_code: str = Field(min_length=1, max_length=64)


class PlexPinPollResponse(BaseModel):
    status: str
    connection: ConnectionSummary | None = None


class PlexLibraryInfo(BaseModel):
    id: str
    title: str
    type: str


class PlexLibrariesResponse(BaseModel):
    libraries: list[PlexLibraryInfo]
    selected_ids: list[str]


class PlexLibrariesUpdateRequest(BaseModel):
    library_ids: list[str] = Field(default_factory=list)
