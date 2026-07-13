"""Map third-party API payloads to ``MediaItem``."""

from __future__ import annotations

import contextlib
from datetime import UTC, datetime
from typing import Any

from plextraktbox.sync.guid import identifiers_from_guids, letterboxd_slug, media_type_from_plex_type
from plextraktbox.sync.media_item import MediaItem, MediaType


def media_item_from_plex_video(video: Any, *, source: str = "plex") -> MediaItem | None:
    """Build a movie ``MediaItem`` from a plexapi video object."""
    media_type = media_type_from_plex_type(getattr(video, "type", "movie"))
    if media_type != MediaType.MOVIE:
        return None

    guids = [str(guid.id) for guid in getattr(video, "guids", []) or []]
    if not guids and getattr(video, "guid", None):
        guids = [str(video.guid)]

    rating_key = str(getattr(video, "ratingKey", "") or "")
    return MediaItem(
        title=str(getattr(video, "title", "") or "Unknown"),
        media_type=MediaType.MOVIE,
        identifiers=identifiers_from_guids(guids),
        rating=_plex_user_rating(video),
        watched=_plex_is_watched(video),
        watched_at=_plex_last_viewed_at(video),
        source=source,
        source_key=f"plex:{rating_key}" if rating_key else "",
    )


def _plex_user_rating(video: Any) -> float | None:
    raw = getattr(video, "userRating", None)
    if raw is None:
        return None
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None
    return value if value > 0 else None


def _plex_is_watched(video: Any) -> bool:
    view_count = getattr(video, "viewCount", 0) or 0
    try:
        return int(view_count) > 0
    except (TypeError, ValueError):
        return False


def _plex_last_viewed_at(video: Any) -> datetime | None:
    raw = getattr(video, "lastViewedAt", None)
    if raw is None:
        return None
    if isinstance(raw, datetime):
        if raw.tzinfo is None:
            return raw.replace(tzinfo=UTC)
        return raw.astimezone(UTC)
    return None


def media_item_from_trakt_movie(
    payload: dict[str, Any],
    *,
    source: str = "trakt",
    watchlisted: bool = False,
    rating: float | None = None,
    watched: bool = False,
    watched_at: datetime | None = None,
) -> MediaItem | None:
    """Build a movie ``MediaItem`` from a Trakt movie object (watchlist/ratings/watched)."""
    movie = payload.get("movie") if "movie" in payload else payload
    if not isinstance(movie, dict):
        return None

    media_type = str(movie.get("type") or "movie").lower()
    if media_type != "movie":
        return None

    ids = movie.get("ids") or {}
    identifiers: dict[str, str] = {}
    if tmdb := ids.get("tmdb"):
        identifiers["tmdb"] = str(tmdb)
    if imdb := ids.get("imdb"):
        identifiers["imdb"] = str(imdb)
    if tvdb := ids.get("tvdb"):
        identifiers["tvdb"] = str(tvdb)

    trakt_id = ids.get("trakt")
    source_key = f"trakt:{trakt_id}" if trakt_id is not None else ""

    resolved_rating = rating
    if resolved_rating is None and "rating" in payload:
        try:
            resolved_rating = float(payload["rating"])
        except (TypeError, ValueError):
            resolved_rating = None

    resolved_watched_at = watched_at
    if resolved_watched_at is None:
        for key in ("last_watched_at", "watched_at"):
            if raw := payload.get(key):
                parsed = _parse_iso_datetime(str(raw))
                if parsed is not None:
                    resolved_watched_at = parsed
                    break

    resolved_watched = watched or resolved_watched_at is not None
    if "plays" in payload:
        with contextlib.suppress(TypeError, ValueError):
            resolved_watched = int(payload["plays"]) > 0

    return MediaItem(
        title=str(movie.get("title") or "Unknown"),
        media_type=MediaType.MOVIE,
        identifiers=identifiers,
        watchlisted=watchlisted,
        rating=resolved_rating,
        watched=resolved_watched,
        watched_at=resolved_watched_at,
        source=source,
        source_key=source_key,
    )


def media_item_from_letterboxd_film(
    *,
    title: str,
    slug: str,
    rating: float | None = None,
    watchlisted: bool = False,
    watched: bool = False,
    watched_at: datetime | None = None,
    identifiers: dict[str, str] | None = None,
) -> MediaItem:
    """Build a movie ``MediaItem`` from scraped Letterboxd list data."""
    merged = dict(identifiers or {})
    return MediaItem(
        title=title,
        media_type=MediaType.MOVIE,
        identifiers=merged,
        watchlisted=watchlisted,
        rating=rating,
        watched=watched,
        watched_at=watched_at,
        source="letterboxd",
        source_key=f"letterboxd:{slug}",
    )


def letterboxd_stars_to_normalized(stars: float) -> float:
    """Convert Letterboxd 0.5–5 stars to Plex/Trakt 0–10 scale."""
    return round(stars * 2, 1)


def parse_letterboxd_rating(raw: str | None) -> float | None:
    if not raw:
        return None
    try:
        stars = float(raw)
    except ValueError:
        return None
    if stars <= 0:
        return None
    return letterboxd_stars_to_normalized(stars)


def film_slug_from_url(url: str) -> str | None:
    return letterboxd_slug(url)


def _parse_iso_datetime(value: str) -> datetime | None:
    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)
