"""Source adapters."""

from plextraktbox.sync.sources.base import NotSupported, Source, SourceCapabilities
from plextraktbox.sync.sources.letterboxd_source import LetterboxdSource
from plextraktbox.sync.sources.memory import MemorySource, movie
from plextraktbox.sync.sources.plex_source import PlexSource
from plextraktbox.sync.sources.trakt_source import TraktSource

__all__ = [
    "LetterboxdSource",
    "MemorySource",
    "NotSupported",
    "PlexSource",
    "Source",
    "SourceCapabilities",
    "TraktSource",
    "movie",
]
