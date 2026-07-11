"""Parse service-native GUIDs into structured identifiers."""

from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urlparse

from plextraktbox.sync.media_item import MediaType

_GUID_RE = re.compile(r"^(?P<scheme>[a-z0-9]+)://(?P<value>.+)$", re.IGNORECASE)
_IMDB_RE = re.compile(r"^tt\d{7,8}$", re.IGNORECASE)


@dataclass(frozen=True)
class Guid:
    scheme: str
    value: str

    def as_identifier(self) -> tuple[str, str] | None:
        scheme = self.scheme.lower()
        if scheme == "tmdb":
            return "tmdb", self.value.split("?")[0]
        if scheme == "imdb":
            value = self.value if _IMDB_RE.match(self.value) else f"tt{self.value}"
            return "imdb", value.lower()
        if scheme == "tvdb":
            return "tvdb", self.value.split("?")[0]
        return None


def parse_guid(raw: str) -> Guid | None:
    raw = raw.strip()
    if not raw:
        return None
    match = _GUID_RE.match(raw)
    if match is None:
        return None
    return Guid(scheme=match.group("scheme"), value=match.group("value"))


def identifiers_from_guids(guids: list[str]) -> dict[str, str]:
    identifiers: dict[str, str] = {}
    for raw in guids:
        parsed = parse_guid(raw)
        if parsed is None:
            continue
        pair = parsed.as_identifier()
        if pair is None:
            continue
        key, value = pair
        identifiers.setdefault(key, value)
    return identifiers


def letterboxd_slug(url: str) -> str | None:
    parsed = urlparse(url)
    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) >= 2 and parts[0] == "film":
        return parts[1].rstrip("/")
    return None


def media_type_from_plex_type(plex_type: str) -> MediaType:
    normalized = plex_type.lower()
    if normalized in {"movie"}:
        return MediaType.MOVIE
    if normalized in {"show"}:
        return MediaType.SHOW
    if normalized in {"episode"}:
        return MediaType.EPISODE
    return MediaType.MOVIE
