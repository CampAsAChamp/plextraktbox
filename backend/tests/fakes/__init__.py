"""Test doubles for sync sources (in-memory; no API credentials)."""

from plextraktbox.sync.sources.base import ReadOnlySourceMixin
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


class FakeLetterboxd(ReadOnlySourceMixin, MemorySource):
    """Read-only Letterboxd fake matching production capabilities."""

    def __init__(self) -> None:
        super().__init__(name="letterboxd", capabilities=READ_ONLY)
