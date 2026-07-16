"""Source adapters."""

from plextraktbox.sync.sources.base import (
    ClientBackedSource,
    NotSupported,
    ReadOnlySourceMixin,
    Source,
    SourceCapabilities,
)
from plextraktbox.sync.sources.letterboxd_source import LetterboxdSource
from plextraktbox.sync.sources.memory import MemorySource, movie
from plextraktbox.sync.sources.plex_source import PlexSource
from plextraktbox.sync.sources.trakt_source import TraktSource

__all__ = [
    "ClientBackedSource",
    "LetterboxdSource",
    "MemorySource",
    "NotSupported",
    "PlexSource",
    "ReadOnlySourceMixin",
    "Source",
    "SourceCapabilities",
    "TraktSource",
    "movie",
]
