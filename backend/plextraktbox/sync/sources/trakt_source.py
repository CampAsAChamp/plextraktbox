"""Trakt source adapter — client-backed fetch (Phase 7), in-memory apply until Phase 8."""

from __future__ import annotations

import asyncio

from plextraktbox.clients import trakt_client
from plextraktbox.sync.media_item import MediaItem
from plextraktbox.sync.sources.memory import MemorySource


class TraktSource(MemorySource):
    def __init__(self, *, client_id: str, access_token: str) -> None:
        super().__init__(name="trakt")
        self._client_id = client_id
        self._access_token = access_token

    async def fetch_watchlist(self) -> list[MediaItem]:
        return await asyncio.to_thread(
            trakt_client.fetch_watchlist_movies,
            self._client_id,
            self._access_token,
        )

    async def fetch_ratings(self) -> list[MediaItem]:
        return await asyncio.to_thread(
            trakt_client.fetch_ratings_movies,
            self._client_id,
            self._access_token,
        )

    async def fetch_watched(self) -> list[MediaItem]:
        return await asyncio.to_thread(
            trakt_client.fetch_watched_movies,
            self._client_id,
            self._access_token,
        )
