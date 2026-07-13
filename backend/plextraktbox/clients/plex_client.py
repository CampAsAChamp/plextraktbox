"""Plex server connection test, PIN-based account linking, and library fetch."""

from __future__ import annotations

import hashlib
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode, urlparse

import httpx
from plexapi.myplex import MyPlexAccount
from plexapi.server import PlexServer

from plextraktbox.clients.base import ConnectionTestResult
from plextraktbox.clients.http_cache import get_cached_requests_session, get_plex_server_requests_session
from plextraktbox.clients.media_mappers import media_item_from_plex_video
from plextraktbox.sync.media_item import MediaItem

PLEX_PINS_URL = "https://plex.tv/api/v2/pins"
PLEX_RESOURCES_URL = "https://plex.tv/api/v2/resources"
PLEX_LINK_URL = "https://plex.tv/link"
PLEX_PRODUCT = "plextraktbox"
PLEX_VERSION = "0.1.0"
PIN_EXPIRES_IN = 1800
PIN_POLL_INTERVAL = 2


def plex_server_ssl_verify(url: str) -> bool:
    """Return whether to verify TLS for a Plex Media Server base URL.

    ``*.plex.direct`` certificates use a Plex-issued CA that fails Python 3.13+
    strict X.509 checks (Basic Constraints not marked critical). Skipping
    verification for those hosts matches PlexTraktSync and other self-hosted tools.
    """
    host = (urlparse(url).hostname or "").lower()
    return not host.endswith(".plex.direct")


@dataclass(frozen=True)
class PlexPinStart:
    pin_id: int
    pin_code: str
    auth_url: str
    verification_url: str
    expires_in: int
    interval: int


@dataclass(frozen=True)
class PlexDiscoveredServer:
    url: str
    token: str
    friendly_name: str
    machine_id: str


@dataclass(frozen=True)
class PlexLibraryInfo:
    id: str
    title: str
    library_type: str


def plex_client_identifier(secret_key: str) -> str:
    """Stable Plex client ID for this deployment (required for PIN auth)."""
    digest = hashlib.sha256(f"plex-client:{secret_key}".encode()).hexdigest()
    return digest[:32]


def _plex_headers(client_identifier: str) -> dict[str, str]:
    return {
        "Accept": "application/json",
        "X-Plex-Product": PLEX_PRODUCT,
        "X-Plex-Version": PLEX_VERSION,
        "X-Plex-Client-Identifier": client_identifier,
        "X-Plex-Platform": "Web",
        "X-Plex-Platform-Version": PLEX_VERSION,
        "X-Plex-Device": "Server",
        "X-Plex-Device-Name": PLEX_PRODUCT,
    }


def _build_auth_url(client_identifier: str, pin_code: str) -> str:
    headers = _plex_headers(client_identifier)
    auth_params = urlencode(
        {
            "clientID": client_identifier,
            "code": pin_code,
            "context[device][product]": headers["X-Plex-Product"],
            "context[device][version]": headers["X-Plex-Version"],
            "context[device][platform]": headers["X-Plex-Platform"],
            "context[device][platformVersion]": headers["X-Plex-Platform-Version"],
            "context[device][device]": headers["X-Plex-Device"],
            "context[device][deviceName]": headers["X-Plex-Device-Name"],
        }
    )
    return f"https://app.plex.tv/auth/#!?{auth_params}"


def start_pin_flow(client_identifier: str) -> PlexPinStart:
    resp = httpx.post(
        PLEX_PINS_URL,
        headers=_plex_headers(client_identifier),
        data={
            "strong": "true",
            "X-Plex-Product": PLEX_PRODUCT,
            "X-Plex-Client-Identifier": client_identifier,
        },
        timeout=15.0,
    )
    resp.raise_for_status()
    data = resp.json()
    pin_id = int(data["id"])
    pin_code = str(data["code"])
    return PlexPinStart(
        pin_id=pin_id,
        pin_code=pin_code,
        auth_url=_build_auth_url(client_identifier, pin_code),
        verification_url=PLEX_LINK_URL,
        expires_in=PIN_EXPIRES_IN,
        interval=PIN_POLL_INTERVAL,
    )


def poll_pin_token(client_identifier: str, pin_id: int, pin_code: str) -> tuple[str, str | None]:
    """Return ``('pending', None)`` or ``('ok', token)`` or raise on fatal error."""
    resp = httpx.get(
        f"{PLEX_PINS_URL}/{pin_id}",
        headers=_plex_headers(client_identifier),
        params={"code": pin_code},
        timeout=15.0,
    )
    if resp.status_code == 404:
        raise ValueError("Plex authorization expired — start again")
    resp.raise_for_status()
    data = resp.json()
    token = data.get("authToken")
    if not token:
        return "pending", None
    return "ok", str(token)


def _rank_connection_urls(connections: list[dict[str, object]]) -> list[str]:
    """Prefer relay/remote URLs so Docker containers can reach home Plex servers."""

    def score(connection: dict[str, object]) -> tuple[int, int]:
        relay = 1 if connection.get("relay") else 0
        local = 1 if connection.get("local") else 0
        https = 1 if str(connection.get("uri", "")).startswith("https") else 0
        # relay first, then remote, then local; prefer https within each tier
        reachability = relay * 2 + (0 if local else 1)
        return (reachability, https)

    ranked = sorted(connections, key=score, reverse=True)
    urls: list[str] = []
    for connection in ranked:
        uri = connection.get("uri")
        if not uri:
            continue
        url = str(uri).rstrip("/")
        if url not in urls:
            urls.append(url)
    return urls


def discover_servers(account_token: str, client_identifier: str) -> list[PlexDiscoveredServer]:
    resp = httpx.get(
        PLEX_RESOURCES_URL,
        headers={**_plex_headers(client_identifier), "X-Plex-Token": account_token},
        params={"includeHttps": 1, "includeRelay": 1, "includeIPv6": 1},
        timeout=15.0,
    )
    resp.raise_for_status()
    resources = resp.json()
    if not isinstance(resources, list):
        raise ValueError("Unexpected Plex resources response")

    servers: list[PlexDiscoveredServer] = []
    for resource in resources:
        if not isinstance(resource, dict):
            continue
        provides = str(resource.get("provides", ""))
        if "server" not in provides:
            continue
        if not resource.get("owned", False):
            continue

        urls = _rank_connection_urls(resource.get("connections", []))
        if not urls:
            continue

        tokens: list[str] = [account_token]
        access_token = resource.get("accessToken")
        if access_token and str(access_token) != account_token:
            tokens.append(str(access_token))

        friendly_name = str(resource.get("name", "Plex Server"))
        machine_id = str(resource.get("clientIdentifier", ""))
        for url in urls:
            for token in tokens:
                servers.append(
                    PlexDiscoveredServer(
                        url=url,
                        token=token,
                        friendly_name=friendly_name,
                        machine_id=machine_id,
                    )
                )
    return servers


def find_connectable_server(
    account_token: str,
    client_identifier: str,
) -> tuple[PlexDiscoveredServer | None, ConnectionTestResult | None]:
    """Try discovered Plex servers until one responds."""
    servers = discover_servers(account_token, client_identifier)
    if not servers:
        return None, None

    last_result: ConnectionTestResult | None = None
    seen: set[tuple[str, str]] = set()
    for candidate in servers:
        key = (candidate.url, candidate.token)
        if key in seen:
            continue
        seen.add(key)

        result = test_connection(candidate.url, candidate.token)
        if result.ok:
            return candidate, result
        last_result = result

    return None, last_result


def pick_best_server(servers: list[PlexDiscoveredServer]) -> PlexDiscoveredServer | None:
    if not servers:
        return None
    return servers[0]


def test_connection(url: str, token: str) -> ConnectionTestResult:
    """Probe ``/identity`` with httpx (same TLS stack as Plex.tv PIN/resources calls)."""
    base = url.rstrip("/")
    verify = plex_server_ssl_verify(base)
    try:
        resp = httpx.get(
            f"{base}/identity",
            headers={"X-Plex-Token": token, "Accept": "application/xml"},
            timeout=10.0,
            verify=verify,
        )
        resp.raise_for_status()
    except httpx.HTTPError as exc:
        return ConnectionTestResult(ok=False, message=f"Plex connection failed: {exc}")
    except Exception as exc:  # noqa: BLE001 — surface unexpected errors to the UI
        return ConnectionTestResult(ok=False, message=f"Plex connection failed: {exc}")

    try:
        root = ET.fromstring(resp.text)
    except ET.ParseError:
        return ConnectionTestResult(
            ok=False,
            message="Plex connection failed: invalid identity response",
        )

    friendly_name = root.attrib.get("friendlyName") or ""
    machine_id = root.attrib.get("machineIdentifier") or ""
    if not machine_id:
        return ConnectionTestResult(
            ok=False,
            message="Plex connection failed: missing machine identifier",
        )

    return ConnectionTestResult(
        ok=True,
        message="Connected to Plex",
        details={"friendly_name": friendly_name, "machine_id": machine_id},
    )


def _plex_server(url: str, token: str) -> PlexServer:
    verify = plex_server_ssl_verify(url)
    session = get_plex_server_requests_session(verify)
    return PlexServer(url.rstrip("/"), token, session=session)


def list_libraries(url: str, token: str) -> list[PlexLibraryInfo]:
    """Return Plex libraries on the connected Plex server."""
    base = url.rstrip("/")
    verify = plex_server_ssl_verify(base)
    resp = httpx.get(
        f"{base}/library/sections",
        headers={"X-Plex-Token": token, "Accept": "application/xml"},
        timeout=30.0,
        verify=verify,
    )
    resp.raise_for_status()

    try:
        root = ET.fromstring(resp.text)
    except ET.ParseError as exc:
        raise ValueError("Plex library list failed: invalid response") from exc

    libraries: list[PlexLibraryInfo] = []
    for directory in root.findall(".//Directory"):
        if str(directory.attrib.get("type", "")).lower() != "movie":
            continue
        section_id = directory.attrib.get("key")
        title = directory.attrib.get("title")
        if not section_id or not title:
            continue
        libraries.append(
            PlexLibraryInfo(
                id=str(section_id),
                title=str(title),
                library_type="movie",
            )
        )
    libraries.sort(key=lambda lib: lib.title.casefold())
    return libraries


def fetch_watchlist_movies(token: str) -> list[MediaItem]:
    """Fetch account-level Plex watchlist movies."""
    session = get_cached_requests_session()
    account = MyPlexAccount(token=token, session=session)
    items: list[MediaItem] = []
    for entry in account.watchlist():
        if str(getattr(entry, "type", "")).lower() != "movie":
            continue
        item = media_item_from_plex_video(entry)
        if item is not None:
            item.watchlisted = True
            items.append(item)
    return items


def fetch_library_movies(
    url: str,
    token: str,
    *,
    library_ids: list[str] | None = None,
) -> list[Any]:
    """Return raw plexapi movie objects from selected libraries (all movie libs when unset)."""
    server = _plex_server(url, token)
    selected = {str(value) for value in library_ids or []}
    movies: list[Any] = []
    for section in server.library.sections():
        if str(getattr(section, "type", "")).lower() != "movie":
            continue
        section_key = str(section.key)
        if selected and section_key not in selected:
            continue
        movies.extend(section.all())
    return movies


def fetch_ratings_movies(
    url: str,
    token: str,
    *,
    library_ids: list[str] | None = None,
) -> list[MediaItem]:
    """Fetch scoped Plex library movies for ratings reconciliation.

    Returns every movie in the selected libraries, including items without a Plex
    rating yet, so Letterboxd ratings can match against the full catalog.
    """
    items: list[MediaItem] = []
    for video in fetch_library_movies(url, token, library_ids=library_ids):
        item = media_item_from_plex_video(video)
        if item is not None:
            items.append(item)
    return items


def fetch_watched_movies(
    url: str,
    token: str,
    *,
    library_ids: list[str] | None = None,
) -> list[MediaItem]:
    """Fetch watched movies from scoped Plex libraries."""
    items: list[MediaItem] = []
    for video in fetch_library_movies(url, token, library_ids=library_ids):
        item = media_item_from_plex_video(video)
        if item is not None and item.watched:
            items.append(item)
    return items
