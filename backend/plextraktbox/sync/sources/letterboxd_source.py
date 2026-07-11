"""Read-only Letterboxd source (Phase 3: in-memory; Phase 7: client fetch)."""

from __future__ import annotations

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


class LetterboxdSource(MemorySource):
    """Letterboxd is read-only — apply_* always raise NotSupported."""

    def __init__(self) -> None:
        super().__init__(name="letterboxd", capabilities=READ_ONLY)

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
