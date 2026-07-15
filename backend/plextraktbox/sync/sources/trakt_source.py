"""Trakt source adapter — client-backed fetch and apply (movies + TV)."""

from __future__ import annotations

import asyncio

from plextraktbox.clients import trakt_client
from plextraktbox.sync.media_item import MediaItem
from plextraktbox.sync.plans import ApplyResult, ChangeAction, PlannedChange
from plextraktbox.sync.sources.apply_helpers import apply_live
from plextraktbox.sync.sources.memory import MemorySource


class TraktSource(MemorySource):
    def __init__(self, *, client_id: str, access_token: str) -> None:
        super().__init__(name="trakt")
        self._client_id = client_id
        self._access_token = access_token

    async def fetch_watchlist(self) -> list[MediaItem]:
        return await asyncio.to_thread(
            trakt_client.fetch_watchlist,
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
            trakt_client.fetch_watched,
            self._client_id,
            self._access_token,
        )

    async def apply_watchlist(
        self,
        changes: list[PlannedChange],
        *,
        dry_run: bool,
    ) -> ApplyResult:
        if not changes:
            return ApplyResult()

        action = changes[0].action

        def apply_batch(batch: list[PlannedChange]) -> None:
            items = [change.item for change in batch]
            if action == ChangeAction.ADD:
                trakt_client.add_watchlist_items(self._client_id, self._access_token, items)
            else:
                trakt_client.remove_watchlist_items(self._client_id, self._access_token, items)

        return await apply_live(changes, dry_run=dry_run, apply_batch=apply_batch)

    async def apply_ratings(
        self,
        changes: list[PlannedChange],
        *,
        dry_run: bool,
    ) -> ApplyResult:
        def apply_batch(batch: list[PlannedChange]) -> None:
            ratings = [(change.item, float(change.new_value)) for change in batch]
            trakt_client.rate_movies(self._client_id, self._access_token, ratings)

        return await apply_live(changes, dry_run=dry_run, apply_batch=apply_batch)

    async def apply_watched(
        self,
        changes: list[PlannedChange],
        *,
        dry_run: bool,
    ) -> ApplyResult:
        # Trakt is the watched source of truth — reconcilers never target Trakt for watched.
        return ApplyResult(skipped=len(changes))
