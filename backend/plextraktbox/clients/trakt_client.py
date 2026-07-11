"""Trakt OAuth device flow and connection test."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import httpx

from plextraktbox.clients.base import ConnectionTestResult

TRAKT_BASE = "https://api.trakt.tv"
TRAKT_HEADERS = {
    "Content-Type": "application/json",
    "trakt-api-version": "2",
}


def _as_utc_aware(value: datetime) -> datetime:
    """Normalize DB datetimes (often naive UTC) for aware comparisons."""
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _token_is_expired(token_expires_at: datetime) -> bool:
    return _as_utc_aware(token_expires_at) <= datetime.now(UTC)


@dataclass(frozen=True)
class TraktTokens:
    access_token: str
    refresh_token: str
    expires_at: datetime | None


@dataclass(frozen=True)
class TraktDeviceStart:
    user_code: str
    device_code: str
    verification_url: str
    expires_in: int
    interval: int


def _headers(client_id: str) -> dict[str, str]:
    return {**TRAKT_HEADERS, "trakt-api-key": client_id}


def start_device_flow(client_id: str) -> TraktDeviceStart:
    resp = httpx.post(
        f"{TRAKT_BASE}/oauth/device/code",
        json={"client_id": client_id},
        headers=_headers(client_id),
        timeout=15.0,
    )
    resp.raise_for_status()
    data = resp.json()
    return TraktDeviceStart(
        user_code=data["user_code"],
        device_code=data["device_code"],
        verification_url=data["verification_url"],
        expires_in=int(data["expires_in"]),
        interval=int(data["interval"]),
    )


def poll_device_token(
    client_id: str,
    client_secret: str,
    device_code: str,
) -> tuple[str, TraktTokens | None]:
    """Return ``('pending', None)`` or ``('ok', tokens)`` or raise on fatal error."""
    resp = httpx.post(
        f"{TRAKT_BASE}/oauth/device/token",
        json={
            "code": device_code,
            "client_id": client_id,
            "client_secret": client_secret,
        },
        headers=_headers(client_id),
        timeout=15.0,
    )
    if resp.status_code == 200:
        data = resp.json()
        expires_at = None
        if "expires_in" in data:
            expires_at = datetime.now(UTC) + timedelta(seconds=int(data["expires_in"]))
        return (
            "ok",
            TraktTokens(
                access_token=data["access_token"],
                refresh_token=data["refresh_token"],
                expires_at=expires_at,
            ),
        )

    try:
        detail = resp.json()
    except ValueError:
        resp.raise_for_status()
        raise

    error = detail.get("error", "")
    if error == "authorization_pending":
        return "pending", None
    if error == "slow_down":
        return "pending", None
    if error == "expired_token":
        raise ValueError("Trakt device code expired — start authorization again")
    raise ValueError(detail.get("error_description") or error or "Trakt authorization failed")


def refresh_access_token(
    client_id: str,
    client_secret: str,
    refresh_token: str,
) -> TraktTokens:
    resp = httpx.post(
        f"{TRAKT_BASE}/oauth/token",
        json={
            "refresh_token": refresh_token,
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "refresh_token",
            "redirect_uri": "urn:ietf:wg:oauth:2.0:oob",
        },
        headers=_headers(client_id),
        timeout=15.0,
    )
    resp.raise_for_status()
    data = resp.json()
    expires_at = None
    if "expires_in" in data:
        expires_at = datetime.now(UTC) + timedelta(seconds=int(data["expires_in"]))
    return TraktTokens(
        access_token=data["access_token"],
        refresh_token=data.get("refresh_token", refresh_token),
        expires_at=expires_at,
    )


def test_connection(
    client_id: str,
    client_secret: str,
    access_token: str,
    refresh_token: str,
    *,
    token_expires_at: datetime | None = None,
) -> tuple[ConnectionTestResult, TraktTokens | None]:
    """Test Trakt access; refresh when expired. Returns result and refreshed tokens if any."""
    tokens: TraktTokens | None = None
    access = access_token

    if token_expires_at is not None and _token_is_expired(token_expires_at):
        try:
            tokens = refresh_access_token(client_id, client_secret, refresh_token)
            access = tokens.access_token
        except httpx.HTTPError as exc:
            return (
                ConnectionTestResult(ok=False, message=f"Trakt token refresh failed: {exc}"),
                None,
            )
        except Exception:  # noqa: BLE001
            return (
                ConnectionTestResult(
                    ok=False,
                    message="Trakt session expired — re-authorize",
                ),
                None,
            )

    try:
        resp = httpx.get(
            f"{TRAKT_BASE}/users/settings",
            headers={**_headers(client_id), "Authorization": f"Bearer {access}"},
            timeout=15.0,
        )
    except httpx.HTTPError as exc:
        return ConnectionTestResult(ok=False, message=f"Trakt request failed: {exc}"), tokens

    if resp.status_code == 401:
        try:
            tokens = refresh_access_token(client_id, client_secret, refresh_token)
            resp = httpx.get(
                f"{TRAKT_BASE}/users/settings",
                headers={
                    **_headers(client_id),
                    "Authorization": f"Bearer {tokens.access_token}",
                },
                timeout=15.0,
            )
        except httpx.HTTPError as exc:
            return (
                ConnectionTestResult(ok=False, message=f"Trakt token refresh failed: {exc}"),
                None,
            )
        except Exception:  # noqa: BLE001
            return (
                ConnectionTestResult(
                    ok=False,
                    message="Trakt session expired — re-authorize",
                ),
                None,
            )

    if resp.status_code != 200:
        return (
            ConnectionTestResult(ok=False, message=f"Trakt returned HTTP {resp.status_code}"),
            tokens,
        )

    data = resp.json()
    username = data.get("user", {}).get("username", "unknown")
    return (
        ConnectionTestResult(
            ok=True,
            message="Connected to Trakt",
            details={"username": username},
        ),
        tokens,
    )
