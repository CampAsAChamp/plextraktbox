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

    def _resolver_with_progress(
        self, data_type: str, *, total: int | None = None
    ) -> IdentifierResolver | None:
        if self._resolve_identifiers is None:
            return None

        resolved = 0
        base = self._resolve_identifiers
        log = self._log
        total_suffix = f"/{total}" if total is not None else ""

        def resolve(slug: str, title: str, year: str | None = None) -> dict[str, str] | None:
            nonlocal resolved
            result = base(slug, title, year)
            resolved += 1
            log.debug(
                "sync.letterboxd.resolve.item",
                message=(
                    f'Matched Letterboxd "{title}"'
                    + (f" ({year})" if year else "")
                    + f" to TMDB: {result or 'unmatched'}"
                ),
                data_type=data_type,
                slug=slug,
                title=title,
                year=year,
                identifiers=result or {},
                resolved=resolved,
                total=total,
            )
            if resolved % _PROGRESS_INTERVAL == 0 or (total is not None and resolved == total):
                log.info(
                    "sync.letterboxd.resolve.progress",
                    message=(f"Matched {resolved}{total_suffix} Letterboxd {data_type} item(s) to TMDB IDs"),
                    data_type=data_type,
                    resolved=resolved,
                    total=total,
                )
            return result

        return resolve

    def _log_resolve_start(self, data_type: str, csv_text: str | None) -> None:
        if self._resolve_identifiers is None:
            return
        count = _csv_row_count(csv_text)
        self._log.info(
            "sync.letterboxd.resolve.start",
            message=(
                f"Matching {count} Letterboxd {data_type} item(s) to TMDB IDs "
                "(Letterboxd CSV has no external IDs; needed to match Plex/Trakt)"
            ),
            data_type=data_type,
            count=count,
        )

    async def fetch_watchlist(self) -> list[MediaItem]:
        export = await self._get_export()
        self._log_resolve_start("watchlist", export.watchlist_csv)
        return letterboxd_client.items_from_watchlist_csv(
            export.watchlist_csv,
            resolve_identifiers=self._resolver_with_progress(
                "watchlist", total=_csv_row_count(export.watchlist_csv)
            ),
        )

    async def fetch_ratings(self) -> list[MediaItem]:
        export = await self._get_export()
        self._log_resolve_start("ratings", export.ratings_csv)
        return letterboxd_client.items_from_ratings_csv(
            export.ratings_csv,
            resolve_identifiers=self._resolver_with_progress(
                "ratings", total=_csv_row_count(export.ratings_csv)
            ),
        )

    async def fetch_watched(self) -> list[MediaItem]:
        export = await self._get_export()
        self._log_resolve_start("watched", export.diary_csv)
        return letterboxd_client.items_from_diary_csv(
            export.diary_csv,
            resolve_identifiers=self._resolver_with_progress(
                "watched", total=_csv_row_count(export.diary_csv)
            ),
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
