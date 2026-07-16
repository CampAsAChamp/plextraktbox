"""Plex library snapshot, indexing, and fetch helpers."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Any

import httpx
from plexapi.myplex import MyPlexAccount
from plexapi.server import PlexServer

from plextraktbox.clients.http_cache import get_cached_requests_session, get_plex_server_requests_session
from plextraktbox.clients.plex_auth import plex_server_ssl_verify
from plextraktbox.sync.media_item import MediaItem, MediaType


def _log():
    from plextraktbox.logging_setup import get_logger

    return get_logger(__name__)


@dataclass
class PlexLibrarySnapshot:
    """Once-per-run Plex library walk shared across fetch and apply."""

    url: str
    token: str
    library_ids: list[str] = field(default_factory=list)
    _movies: list[Any] | None = field(default=None, init=False, repr=False)
    _shows: list[Any] | None = field(default=None, init=False, repr=False)
    _movie_index: dict[str, Any] | None = field(default=None, init=False, repr=False)
    _episode_index: dict[str, Any] | None = field(default=None, init=False, repr=False)

    def movies(self) -> list[Any]:
        if self._movies is None:
            from plextraktbox.clients import plex_client

            self._movies = plex_client._fetch_library_entries(
                self.url,
                self.token,
                library_type="movie",
                library_ids=self.library_ids,
            )
            _log().info(
                "sync.plex.library.loaded",
                message=f"Loaded Plex library movies once for this run ({len(self._movies)} item(s))",
                library_type="movie",
                count=len(self._movies),
            )
        return self._movies

    def shows(self) -> list[Any]:
        if self._shows is None:
            from plextraktbox.clients import plex_client

            self._shows = plex_client._fetch_library_entries(
                self.url,
                self.token,
                library_type="show",
                library_ids=self.library_ids,
            )
            _log().info(
                "sync.plex.library.loaded",
                message=f"Loaded Plex library shows once for this run ({len(self._shows)} item(s))",
                library_type="show",
                count=len(self._shows),
            )
        return self._shows

    def movie_index(self) -> dict[str, Any]:
        if self._movie_index is None:
            self._movie_index = _index_videos_by_match_key(self.movies())
        return self._movie_index

    def episode_index(self) -> dict[str, Any]:
        if self._episode_index is None:
            self._episode_index = _index_episodes_by_match_key(self.shows())
        return self._episode_index


def _index_videos_by_match_key(videos: list[Any]) -> dict[str, Any]:
    from plextraktbox.clients.media_mappers import media_item_from_plex_video

    index: dict[str, Any] = {}
    for video in videos:
        item = media_item_from_plex_video(video)
        if item is None:
            continue
        match_key = item.match_key()
        if match_key:
            index[match_key] = video
    return index


def _index_episodes_by_match_key(shows: list[Any]) -> dict[str, Any]:
    from plextraktbox.clients.media_mappers import (
        media_item_from_plex_episode,
        media_item_from_plex_video,
    )

    index: dict[str, Any] = {}
    for show_obj in shows:
        show_item = media_item_from_plex_video(show_obj)
        if show_item is None or not show_item.identifiers:
            continue
        show_ids = dict(show_item.identifiers)
        show_title = show_item.title
        for episode_obj in show_obj.episodes():
            item = media_item_from_plex_episode(
                episode_obj,
                show_identifiers=show_ids,
                show_title=show_title,
            )
            if item is None:
                continue
            match_key = item.match_key()
            if match_key:
                index[match_key] = episode_obj
    return index


@dataclass(frozen=True)
class PlexLibraryInfo:
    id: str
    title: str
    library_type: str


def _plex_server(url: str, token: str) -> PlexServer:
    verify = plex_server_ssl_verify(url)
    session = get_plex_server_requests_session(verify)
    return PlexServer(url.rstrip("/"), token, session=session)


def list_libraries(url: str, token: str) -> list[PlexLibraryInfo]:
    """Return Plex libraries on the connected Plex server."""
    base = url.rstrip("/")
    verify = plex_server_ssl_verify(base)
    try:
        resp = httpx.get(
            f"{base}/library/sections",
            headers={"X-Plex-Token": token, "Accept": "application/xml"},
            timeout=30.0,
            verify=verify,
        )
        resp.raise_for_status()
    except httpx.HTTPError as exc:
        raise ValueError(f"Plex library list failed: {exc}") from exc

    try:
        root = ET.fromstring(resp.text)
    except ET.ParseError as exc:
        raise ValueError("Plex library list failed: invalid response") from exc

    libraries: list[PlexLibraryInfo] = []
    for directory in root.findall(".//Directory"):
        library_type = str(directory.attrib.get("type", "")).lower()
        if library_type not in {"movie", "show"}:
            continue
        section_id = directory.attrib.get("key")
        title = directory.attrib.get("title")
        if not section_id or not title:
            continue
        libraries.append(
            PlexLibraryInfo(
                id=str(section_id),
                title=str(title),
                library_type=library_type,
            )
        )
    libraries.sort(key=lambda lib: lib.title.casefold())
    return libraries


def fetch_watchlist_movies(token: str) -> list[MediaItem]:
    """Fetch account-level Plex watchlist movies."""
    return [item for item in fetch_watchlist(token) if item.media_type == MediaType.MOVIE]


def fetch_watchlist(token: str) -> list[MediaItem]:
    """Fetch account-level Plex watchlist movies and shows."""
    from plextraktbox.clients.media_mappers import media_item_from_plex_video

    session = get_cached_requests_session()
    account = MyPlexAccount(token=token, session=session)
    items: list[MediaItem] = []
    for entry in account.watchlist():
        entry_type = str(getattr(entry, "type", "")).lower()
        if entry_type not in {"movie", "show"}:
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
    snapshot: PlexLibrarySnapshot | None = None,
) -> list[Any]:
    """Return raw plexapi movie objects from selected libraries (all movie libs when unset)."""
    if snapshot is not None:
        return snapshot.movies()
    return _fetch_library_entries(url, token, library_type="movie", library_ids=library_ids)


def fetch_library_shows(
    url: str,
    token: str,
    *,
    library_ids: list[str] | None = None,
    snapshot: PlexLibrarySnapshot | None = None,
) -> list[Any]:
    """Return raw plexapi show objects from selected libraries (all show libs when unset)."""
    if snapshot is not None:
        return snapshot.shows()
    return _fetch_library_entries(url, token, library_type="show", library_ids=library_ids)


def _fetch_library_entries(
    url: str,
    token: str,
    *,
    library_type: str,
    library_ids: list[str] | None = None,
) -> list[Any]:
    server = _plex_server(url, token)
    selected = {str(value) for value in library_ids or []}
    entries: list[Any] = []
    for section in server.library.sections():
        if str(getattr(section, "type", "")).lower() != library_type:
            continue
        section_key = str(section.key)
        if selected and section_key not in selected:
            continue
        entries.extend(section.all())
    return entries


def fetch_library_episodes(
    url: str,
    token: str,
    *,
    library_ids: list[str] | None = None,
    snapshot: PlexLibrarySnapshot | None = None,
) -> list[MediaItem]:
    """Return episode ``MediaItem``s from selected show libraries."""
    from plextraktbox.clients.media_mappers import (
        media_item_from_plex_episode,
        media_item_from_plex_video,
    )

    items: list[MediaItem] = []
    for show_obj in fetch_library_shows(url, token, library_ids=library_ids, snapshot=snapshot):
        show_item = media_item_from_plex_video(show_obj)
        if show_item is None or not show_item.identifiers:
            continue
        show_title = show_item.title
        show_ids = dict(show_item.identifiers)
        for episode_obj in show_obj.episodes():
            item = media_item_from_plex_episode(
                episode_obj,
                show_identifiers=show_ids,
                show_title=show_title,
            )
            if item is not None:
                items.append(item)
    return items


def fetch_ratings_movies(
    url: str,
    token: str,
    *,
    library_ids: list[str] | None = None,
    snapshot: PlexLibrarySnapshot | None = None,
) -> list[MediaItem]:
    """Fetch scoped Plex library movies for ratings reconciliation.

    Returns every movie in the selected libraries, including items without a Plex
    rating yet, so Letterboxd ratings can match against the full catalog.
    """
    from plextraktbox.clients import plex_client
    from plextraktbox.clients.media_mappers import media_item_from_plex_video

    items: list[MediaItem] = []
    for video in plex_client.fetch_library_movies(url, token, library_ids=library_ids, snapshot=snapshot):
        item = media_item_from_plex_video(video)
        if item is not None:
            items.append(item)
    return items


def fetch_watched_movies(
    url: str,
    token: str,
    *,
    library_ids: list[str] | None = None,
    snapshot: PlexLibrarySnapshot | None = None,
) -> list[MediaItem]:
    """Fetch scoped Plex library movies for watched reconciliation.

    Includes unwatched library movies so Trakt→Plex can plan mark-watched updates.
    """
    from plextraktbox.clients.media_mappers import media_item_from_plex_video

    items: list[MediaItem] = []
    for video in fetch_library_movies(url, token, library_ids=library_ids, snapshot=snapshot):
        item = media_item_from_plex_video(video)
        if item is not None:
            items.append(item)
    return items


def fetch_watched(
    url: str,
    token: str,
    *,
    library_ids: list[str] | None = None,
    snapshot: PlexLibrarySnapshot | None = None,
) -> list[MediaItem]:
    """Fetch scoped Plex library movies and episodes for watched reconciliation."""
    return fetch_watched_movies(
        url, token, library_ids=library_ids, snapshot=snapshot
    ) + fetch_library_episodes(url, token, library_ids=library_ids, snapshot=snapshot)


def _library_videos_by_match_key(
    url: str,
    token: str,
    *,
    library_ids: list[str] | None = None,
    snapshot: PlexLibrarySnapshot | None = None,
) -> dict[str, Any]:
    """Index scoped library movies by TMDB/IMDb/TVDB match key."""
    if snapshot is not None:
        return snapshot.movie_index()
    return _index_videos_by_match_key(fetch_library_movies(url, token, library_ids=library_ids))


def _library_episodes_by_match_key(
    url: str,
    token: str,
    *,
    library_ids: list[str] | None = None,
    snapshot: PlexLibrarySnapshot | None = None,
) -> dict[str, Any]:
    """Index scoped library episodes by show-id + S/E match key."""
    if snapshot is not None:
        return snapshot.episode_index()
    return _index_episodes_by_match_key(fetch_library_shows(url, token, library_ids=library_ids))


def _find_library_video(
    index: dict[str, Any],
    item: MediaItem,
) -> Any:
    match_key = item.match_key()
    if match_key and match_key in index:
        return index[match_key]
    kind = "Episode" if item.media_type == MediaType.EPISODE else "Movie"
    raise ValueError(f"{kind} {item.title!r} not found in scoped Plex libraries")
