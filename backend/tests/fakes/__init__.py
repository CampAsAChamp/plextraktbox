"""Test doubles for sync sources (in-memory; no API credentials)."""

from plextraktbox.sync.plans import ApplyResult, PlannedChange
from plextraktbox.sync.sources.base import NotSupported, SourceCapabilities
from plextraktbox.sync.sources.letterboxd_source import LetterboxdSource, READ_ONLY
from plextraktbox.sync.sources.memory import MemorySource, episode, movie, show
from plextraktbox.sync.sources.plex_source import PlexSource
from plextraktbox.sync.sources.trakt_source import TraktSource

__all__ = [
    "FakeLetterboxd",
    "FakePlex",
    "FakeTrakt",
    "LetterboxdSource",
    "MemorySource",
    "PlexSource",
    "TraktSource",
    "episode",
    "movie",
    "show",
]


class FakePlex(MemorySource):
    def __init__(self) -> None:
        super().__init__(name="plex")


class FakeTrakt(MemorySource):
    def __init__(self) -> None:
        super().__init__(name="trakt")


class FakeLetterboxd(MemorySource):
    """Read-only Letterboxd fake matching production capabilities."""

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
