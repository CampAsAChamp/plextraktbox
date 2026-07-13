"""Plex source adapter — client-backed fetch (Phase 7), in-memory apply until Phase 8."""

from __future__ import annotations

import asyncio

from plextraktbox.clients import plex_client
from plextraktbox.sync.media_item import MediaItem
from plextraktbox.sync.sources.memory import MemorySource


class PlexSource(MemorySource):
    def __init__(
        self,
        *,
        url: str,
        token: str,
        library_ids: list[str] | None = None,
    ) -> None:
        super().__init__(name="plex")
        self._url = url.rstrip("/")
        self._token = token
        self._library_ids = list(library_ids or [])

    async def fetch_watchlist(self) -> list[MediaItem]:
        return await asyncio.to_thread(plex_client.fetch_watchlist_movies, self._token)

    async def fetch_ratings(self) -> list[MediaItem]:
        return await asyncio.to_thread(
            plex_client.fetch_ratings_movies,
            self._url,
            self._token,
            library_ids=self._library_ids,
        )

    async def fetch_watched(self) -> list[MediaItem]:
        return await asyncio.to_thread(
            plex_client.fetch_watched_movies,
            self._url,
            self._token,
            library_ids=self._library_ids,
        )
