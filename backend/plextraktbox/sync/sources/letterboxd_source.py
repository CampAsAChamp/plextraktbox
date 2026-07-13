"""Read-only Letterboxd source — client-backed fetch (Phase 7)."""

from __future__ import annotations

import asyncio
from collections.abc import Callable

import structlog

from plextraktbox.clients import letterboxd_client
from plextraktbox.clients.letterboxd_client import LetterboxdExport
from plextraktbox.sync.media_item import MediaItem
from plextraktbox.sync.plans import ApplyResult, PlannedChange
from plextraktbox.sync.sources.base import NotSupported, SourceCapabilities
from plextraktbox.sync.sources.memory import MemorySource

READ_ONLY = SourceCapabilities(
    watchlist_read=True,
    watchlist_write=False,
    ratings_read=True,
    ratings_write=False,
    watched_read=True,
    watched_write=False,
)

IdentifierResolver = Callable[[str, str, str | None], dict[str, str] | None]
_PROGRESS_INTERVAL = 25


class LetterboxdSource(MemorySource):
    """Letterboxd is read-only — apply_* always raise NotSupported."""

    def __init__(
        self,
        *,
        username: str,
        password: str,
        resolve_identifiers: IdentifierResolver | None = None,
        log: structlog.stdlib.BoundLogger | None = None,
    ) -> None:
        super().__init__(name="letterboxd", capabilities=READ_ONLY)
        self._username = username
        self._password = password
        self._resolve_identifiers = resolve_identifiers
        self._log = log or structlog.get_logger("sync.letterboxd")
        self._export: LetterboxdExport | None = None

    async def _get_export(self) -> LetterboxdExport:
        if self._export is None:
            self._log.info(
                "sync.letterboxd.export.start",
                message="Downloading Letterboxd CSV export (login + ZIP)",
            )
            self._export = await asyncio.to_thread(
                letterboxd_client.download_export,
                self._username,
                self._password,
            )
            ratings_count = _csv_row_count(self._export.ratings_csv)
            watchlist_count = _csv_row_count(self._export.watchlist_csv)
            diary_count = _csv_row_count(self._export.diary_csv)
            self._log.info(
                "sync.letterboxd.export.done",
                message=(
                    "Letterboxd export ready"
                    f" (ratings={ratings_count}, watchlist={watchlist_count}, diary={diary_count})"
                ),
                ratings_count=ratings_count,
                watchlist_count=watchlist_count,
                diary_count=diary_count,
            )
        return self._export

    def _resolver_with_progress(self, data_type: str) -> IdentifierResolver | None:
        if self._resolve_identifiers is None:
            return None

        resolved = 0
        base = self._resolve_identifiers
        log = self._log

        def resolve(slug: str, title: str, year: str | None = None) -> dict[str, str] | None:
            nonlocal resolved
            result = base(slug, title, year)
            resolved += 1
            if resolved % _PROGRESS_INTERVAL == 0:
                log.info(
                    "sync.letterboxd.resolve.progress",
                    message=f"Resolved TMDB IDs for {resolved} {data_type} item(s)",
                    data_type=data_type,
                    resolved=resolved,
                )
            return result

        return resolve

    async def fetch_watchlist(self) -> list[MediaItem]:
        export = await self._get_export()
        return letterboxd_client.items_from_watchlist_csv(
            export.watchlist_csv,
            resolve_identifiers=self._resolver_with_progress("watchlist"),
        )

    async def fetch_ratings(self) -> list[MediaItem]:
        export = await self._get_export()
        return letterboxd_client.items_from_ratings_csv(
            export.ratings_csv,
            resolve_identifiers=self._resolver_with_progress("ratings"),
        )

    async def fetch_watched(self) -> list[MediaItem]:
        export = await self._get_export()
        return letterboxd_client.items_from_diary_csv(
            export.diary_csv,
            resolve_identifiers=self._resolver_with_progress("watched"),
        )

    async def apply_watchlist(
        self,
        changes: list[PlannedChange],
        *,
        dry_run: bool,
    ) -> ApplyResult:
        raise NotSupported("letterboxd does not support watchlist writes")

    async def apply_ratings(
        self,
        changes: list[PlannedChange],
        *,
        dry_run: bool,
    ) -> ApplyResult:
        raise NotSupported("letterboxd does not support ratings writes")

    async def apply_watched(
        self,
        changes: list[PlannedChange],
        *,
        dry_run: bool,
    ) -> ApplyResult:
        raise NotSupported("letterboxd does not support watched writes")


def _csv_row_count(csv_text: str | None) -> int:
    if not csv_text:
        return 0
    lines = [line for line in csv_text.splitlines() if line.strip()]
    return max(0, len(lines) - 1)
