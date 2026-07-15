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


def format_episode_title(show_title: str, season: int, episode: int) -> str:
    """Human-readable episode title for logs and unmatched reports."""
    return f"{show_title} S{season:02d}E{episode:02d}"


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
    season: int | None = None
    episode: int | None = None

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
        base = f"{key}:{value}"
        if self.media_type == MediaType.EPISODE and self.season is not None and self.episode is not None:
            return f"{base}:s{self.season}e{self.episode}"
        return base
