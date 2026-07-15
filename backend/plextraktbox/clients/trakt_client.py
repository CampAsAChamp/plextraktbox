"""Trakt OAuth device flow, connection test, and sync fetch."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx

from plextraktbox.clients.base import ConnectionTestResult
from plextraktbox.clients.media_mappers import (
    media_item_from_trakt_episode,
    media_item_from_trakt_movie,
    media_item_from_trakt_show,
)
from plextraktbox.sync.media_item import MediaItem, MediaType

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


def _auth_headers(client_id: str, access_token: str) -> dict[str, str]:
    return {**_headers(client_id), "Authorization": f"Bearer {access_token}"}


def _trakt_get(
    client_id: str,
    access_token: str,
    path: str,
    *,
    params: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    resp = httpx.get(
        f"{TRAKT_BASE}{path}",
        headers=_auth_headers(client_id, access_token),
        params=params,
        timeout=30.0,
    )
    resp.raise_for_status()
    data = resp.json()
    if not isinstance(data, list):
        raise ValueError(f"Unexpected Trakt response for {path}")
    return data


def fetch_watchlist_movies(client_id: str, access_token: str) -> list[MediaItem]:
    rows = _trakt_get(
        client_id,
        access_token,
        "/sync/watchlist",
        params={"type": "movies"},
    )
    items: list[MediaItem] = []
    for row in rows:
        item = media_item_from_trakt_movie(row, watchlisted=True)
        if item is not None:
            items.append(item)
    return items


def fetch_watchlist_shows(client_id: str, access_token: str) -> list[MediaItem]:
    rows = _trakt_get(
        client_id,
        access_token,
        "/sync/watchlist",
        params={"type": "shows"},
    )
    items: list[MediaItem] = []
    for row in rows:
        item = media_item_from_trakt_show(row, watchlisted=True)
        if item is not None:
            items.append(item)
    return items


def fetch_watchlist(client_id: str, access_token: str) -> list[MediaItem]:
    """Fetch Trakt watchlist movies and shows."""
    return fetch_watchlist_movies(client_id, access_token) + fetch_watchlist_shows(client_id, access_token)


def fetch_ratings_movies(client_id: str, access_token: str) -> list[MediaItem]:
    rows = _trakt_get(client_id, access_token, "/sync/ratings/movies")
    items: list[MediaItem] = []
    for row in rows:
        item = media_item_from_trakt_movie(row)
        if item is not None and item.rating is not None:
            items.append(item)
    return items


def fetch_watched_movies(client_id: str, access_token: str) -> list[MediaItem]:
    rows = _trakt_get(
        client_id,
        access_token,
        "/sync/watched/movies",
        params={"extended": "full"},
    )
    items: list[MediaItem] = []
    for row in rows:
        item = media_item_from_trakt_movie(row, watched=True)
        if item is not None:
            items.append(item)
    return items


def fetch_watched_episodes(client_id: str, access_token: str) -> list[MediaItem]:
    """Expand Trakt watched shows into episode-level ``MediaItem``s."""
    rows = _trakt_get(
        client_id,
        access_token,
        "/sync/watched/shows",
        params={"extended": "full"},
    )
    items: list[MediaItem] = []
    for row in rows:
        show = row.get("show")
        if not isinstance(show, dict):
            continue
        for season in row.get("seasons") or []:
            if not isinstance(season, dict):
                continue
            try:
                season_num = int(season["number"])
            except KeyError, TypeError, ValueError:
                continue
            for ep in season.get("episodes") or []:
                if not isinstance(ep, dict):
                    continue
                try:
                    episode_num = int(ep["number"])
                except KeyError, TypeError, ValueError:
                    continue
                watched_at = None
                if raw := ep.get("last_watched_at"):
                    watched_at = _parse_iso_datetime(str(raw))
                item = media_item_from_trakt_episode(
                    show=show,
                    season=season_num,
                    episode=episode_num,
                    watched_at=watched_at,
                )
                if item is not None:
                    items.append(item)
    return items


def fetch_watched(client_id: str, access_token: str) -> list[MediaItem]:
    """Fetch Trakt watched movies and episodes."""
    return fetch_watched_movies(client_id, access_token) + fetch_watched_episodes(client_id, access_token)


def _parse_iso_datetime(value: str) -> datetime | None:
    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _trakt_ids(item: MediaItem) -> dict[str, int | str]:
    """Build Trakt ``ids`` object from a ``MediaItem`` (requires TMDB, IMDb, or TVDB)."""
    ids: dict[str, int | str] = {}
    if tmdb := item.identifiers.get("tmdb"):
        ids["tmdb"] = int(tmdb)
    if imdb := item.identifiers.get("imdb"):
        ids["imdb"] = imdb
    if tvdb := item.identifiers.get("tvdb"):
        ids["tvdb"] = int(tvdb)
    if not ids:
        raise ValueError(f"No Trakt-compatible ids for {item.title!r}")
    return ids


def _trakt_movie_ids(item: MediaItem) -> dict[str, int | str]:
    """Build Trakt ``ids`` object from a movie ``MediaItem`` (requires TMDB or IMDb)."""
    ids: dict[str, int | str] = {}
    if tmdb := item.identifiers.get("tmdb"):
        ids["tmdb"] = int(tmdb)
    if imdb := item.identifiers.get("imdb"):
        ids["imdb"] = imdb
    if not ids:
        raise ValueError(f"No Trakt-compatible ids for {item.title!r}")
    return ids


def _trakt_post(
    client_id: str,
    access_token: str,
    path: str,
    body: dict[str, Any],
) -> dict[str, Any]:
    resp = httpx.post(
        f"{TRAKT_BASE}{path}",
        headers=_auth_headers(client_id, access_token),
        json=body,
        timeout=30.0,
    )
    resp.raise_for_status()
    data = resp.json()
    if not isinstance(data, dict):
        raise ValueError(f"Unexpected Trakt response for {path}")
    return data


def _partition_watchlist_items(
    items: list[MediaItem],
) -> tuple[list[MediaItem], list[MediaItem]]:
    movies = [item for item in items if item.media_type == MediaType.MOVIE]
    shows = [item for item in items if item.media_type == MediaType.SHOW]
    return movies, shows


def add_watchlist_movies(client_id: str, access_token: str, items: list[MediaItem]) -> None:
    """Add movies to the user's Trakt watchlist."""
    add_watchlist_items(client_id, access_token, items)


def add_watchlist_items(client_id: str, access_token: str, items: list[MediaItem]) -> None:
    """Add movies and shows to the user's Trakt watchlist."""
    if not items:
        return
    movies, shows = _partition_watchlist_items(items)
    body: dict[str, Any] = {}
    if movies:
        body["movies"] = [{"ids": _trakt_movie_ids(item)} for item in movies]
    if shows:
        body["shows"] = [{"ids": _trakt_ids(item)} for item in shows]
    if not body:
        return
    response = _trakt_post(client_id, access_token, "/sync/watchlist", body)
    not_found = response.get("not_found") or {}
    missing_movies = not_found.get("movies") or []
    missing_shows = not_found.get("shows") or []
    if missing_movies or missing_shows:
        raise ValueError(
            f"Trakt could not resolve {len(missing_movies)} watchlist movie(s) "
            f"and {len(missing_shows)} show(s)"
        )


def remove_watchlist_movies(client_id: str, access_token: str, items: list[MediaItem]) -> None:
    """Remove movies from the user's Trakt watchlist."""
    remove_watchlist_items(client_id, access_token, items)


def remove_watchlist_items(client_id: str, access_token: str, items: list[MediaItem]) -> None:
    """Remove movies and shows from the user's Trakt watchlist."""
    if not items:
        return
    movies, shows = _partition_watchlist_items(items)
    body: dict[str, Any] = {}
    if movies:
        body["movies"] = [{"ids": _trakt_movie_ids(item)} for item in movies]
    if shows:
        body["shows"] = [{"ids": _trakt_ids(item)} for item in shows]
    if not body:
        return
    _trakt_post(client_id, access_token, "/sync/watchlist/remove", body)


def rate_movies(
    client_id: str,
    access_token: str,
    ratings: list[tuple[MediaItem, float]],
) -> None:
    """Set movie ratings on Trakt (0–10 scale)."""
    if not ratings:
        return
    movies: list[dict[str, Any]] = []
    for item, rating in ratings:
        movies.append({"rating": rating, "ids": _trakt_movie_ids(item)})
    response = _trakt_post(
        client_id,
        access_token,
        "/sync/ratings",
        {"movies": movies},
    )
    not_found = (response.get("not_found") or {}).get("movies") or []
    if not_found:
        raise ValueError(f"Trakt could not resolve {len(not_found)} rated movie(s)")
