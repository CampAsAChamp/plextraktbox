"""Service-agnostic media representation for sync."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum


class MediaType(StrEnum):
    MOVIE = "movie"
    SHOW = "show"
    EPISODE = "episode"


IDENTIFIER_PRIORITY = ("tmdb", "imdb", "tvdb")


@dataclass
class MediaItem:
    """Normalized item from any connected service."""

    title: str
    media_type: MediaType
    identifiers: dict[str, str] = field(default_factory=dict)
    watchlisted: bool = False
    rating: float | None = None  # normalized 0–10
    watched: bool = False
    watched_at: datetime | None = None
    source: str = ""
    source_key: str = ""

    def best_identifier(self) -> tuple[str, str] | None:
        for key in IDENTIFIER_PRIORITY:
            if value := self.identifiers.get(key):
                return key, value
        return None

    def match_key(self) -> str | None:
        pair = self.best_identifier()
        if pair is None:
            return None
        key, value = pair
        return f"{key}:{value}"
