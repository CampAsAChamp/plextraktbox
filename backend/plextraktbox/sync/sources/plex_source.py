"""Plex source adapter — client-backed fetch and apply (movies + TV)."""

from __future__ import annotations

import asyncio

from plextraktbox.clients import plex_client
from plextraktbox.sync.media_item import MediaItem
from plextraktbox.sync.plans import ApplyResult, ChangeAction, PlannedChange
from plextraktbox.sync.sources.apply_helpers import apply_live
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
        self._library = plex_client.PlexLibrarySnapshot(
            url=self._url,
            token=self._token,
            library_ids=self._library_ids,
        )

    async def fetch_watchlist(self) -> list[MediaItem]:
        return await asyncio.to_thread(plex_client.fetch_watchlist, self._token)

    async def fetch_ratings(self) -> list[MediaItem]:
        return await asyncio.to_thread(
            plex_client.fetch_ratings_movies,
            self._url,
            self._token,
            library_ids=self._library_ids,
            snapshot=self._library,
        )

    async def fetch_watched(self) -> list[MediaItem]:
        return await asyncio.to_thread(
            plex_client.fetch_watched,
            self._url,
            self._token,
            library_ids=self._library_ids,
            snapshot=self._library,
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
                plex_client.add_watchlist_items(self._token, items)
            else:
                plex_client.remove_watchlist_items(self._token, items)

        return await apply_live(changes, dry_run=dry_run, apply_batch=apply_batch)

    async def apply_ratings(
        self,
        changes: list[PlannedChange],
        *,
        dry_run: bool,
    ) -> ApplyResult:
        if not changes:
            return ApplyResult()
        if dry_run:
            return ApplyResult(applied=len(changes))

        ratings = [(change.item, float(change.new_value)) for change in changes]

        def apply() -> tuple[int, int, int]:
            return plex_client.rate_movies_with_discover_fallback(
                self._url,
                self._token,
                ratings,
                library_ids=self._library_ids,
                snapshot=self._library,
            )

        library_applied, discover_applied, errors = await asyncio.to_thread(apply)
        return ApplyResult(applied=library_applied + discover_applied, errors=errors)

    async def apply_watched(
        self,
        changes: list[PlannedChange],
        *,
        dry_run: bool,
    ) -> ApplyResult:
        def apply_batch(batch: list[PlannedChange]) -> None:
            plex_client.mark_library_items_watched(
                self._url,
                self._token,
                [change.item for change in batch],
                library_ids=self._library_ids,
                snapshot=self._library,
            )

        return await apply_live(changes, dry_run=dry_run, apply_batch=apply_batch)
