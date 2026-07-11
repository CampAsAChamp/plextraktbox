"""Test doubles for sync sources."""

from plextraktbox.sync.sources.letterboxd_source import LetterboxdSource
from plextraktbox.sync.sources.memory import MemorySource, movie
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
    "movie",
]

FakePlex = PlexSource
FakeTrakt = TraktSource
FakeLetterboxd = LetterboxdSource
