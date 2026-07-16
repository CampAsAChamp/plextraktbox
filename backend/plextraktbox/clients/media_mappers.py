"""Map third-party API payloads to ``MediaItem``."""

from __future__ import annotations

import contextlib
from datetime import datetime
from typing import Any

from plextraktbox.sync.guid import identifiers_from_guids, letterboxd_slug, media_type_from_plex_type
from plextraktbox.sync.media_item import MediaItem, MediaType, format_episode_title
from plextraktbox.utils.datetime import as_utc_datetime, parse_iso_datetime
from plextraktbox.utils.rating import letterboxd_to_normalized


def _plex_guids(video: Any) -> list[str]:
    guids = [str(guid.id) for guid in getattr(video, "guids", []) or []]
    if not guids and getattr(video, "guid", None):
        guids = [str(video.guid)]
    return guids


def media_item_from_plex_video(video: Any, *, source: str = "plex") -> MediaItem | None:
    """Build a movie or show ``MediaItem`` from a plexapi video/show object."""
    media_type = media_type_from_plex_type(getattr(video, "type", "movie"))
    if media_type == MediaType.EPISODE:
        return media_item_from_plex_episode(video, source=source)
    if media_type not in {MediaType.MOVIE, MediaType.SHOW}:
        return None

    rating_key = str(getattr(video, "ratingKey", "") or "")
    return MediaItem(
        title=str(getattr(video, "title", "") or "Unknown"),
        media_type=media_type,
        identifiers=identifiers_from_guids(_plex_guids(video)),
        rating=_plex_user_rating(video),
        watched=_plex_is_watched(video),
        watched_at=_plex_last_viewed_at(video),
        source=source,
        source_key=f"plex:{rating_key}" if rating_key else "",
    )


def media_item_from_plex_episode(
    video: Any,
    *,
    source: str = "plex",
    show_identifiers: dict[str, str] | None = None,
    show_title: str | None = None,
) -> MediaItem | None:
    """Build an episode ``MediaItem`` using show-level identifiers + S/E numbers."""
    season_raw = getattr(video, "parentIndex", None)
    if season_raw is None:
        season_raw = getattr(video, "seasonNumber", None)
    episode_raw = getattr(video, "index", None)
    if episode_raw is None:
        episode_raw = getattr(video, "episodeNumber", None)
    if season_raw is None or episode_raw is None:
        return None
    try:
        season = int(season_raw)
        episode_num = int(episode_raw)
    except TypeError, ValueError:
        return None

    resolved_show_title = str(
        show_title or getattr(video, "grandparentTitle", "") or getattr(video, "showTitle", "") or "Unknown"
    )
    identifiers = dict(show_identifiers or {})
    if not identifiers:
        identifiers = identifiers_from_guids(_plex_guids(video))
    if not identifiers:
        return None

    rating_key = str(getattr(video, "ratingKey", "") or "")
    return MediaItem(
        title=format_episode_title(resolved_show_title, season, episode_num),
        media_type=MediaType.EPISODE,
        identifiers=identifiers,
        watched=_plex_is_watched(video),
        watched_at=_plex_last_viewed_at(video),
        source=source,
        source_key=f"plex:{rating_key}" if rating_key else "",
        season=season,
        episode=episode_num,
    )


def _plex_user_rating(video: Any) -> float | None:
    raw = getattr(video, "userRating", None)
    if raw is None:
        return None
    try:
        value = float(raw)
    except TypeError, ValueError:
        return None
    return value if value > 0 else None


def _plex_is_watched(video: Any) -> bool:
    view_count = getattr(video, "viewCount", 0) or 0
    try:
        return int(view_count) > 0
    except TypeError, ValueError:
        return False


def _plex_last_viewed_at(video: Any) -> datetime | None:
    raw = getattr(video, "lastViewedAt", None)
    if raw is None:
        return None
    if isinstance(raw, datetime):
        return as_utc_datetime(raw)
    return None


def _trakt_ids(ids: dict[str, Any]) -> dict[str, str]:
    identifiers: dict[str, str] = {}
    if tmdb := ids.get("tmdb"):
        identifiers["tmdb"] = str(tmdb)
    if imdb := ids.get("imdb"):
        identifiers["imdb"] = str(imdb)
    if tvdb := ids.get("tvdb"):
        identifiers["tvdb"] = str(tvdb)
    return identifiers


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
    identifiers = _trakt_ids(ids if isinstance(ids, dict) else {})

    trakt_id = ids.get("trakt") if isinstance(ids, dict) else None
    source_key = f"trakt:{trakt_id}" if trakt_id is not None else ""

    resolved_rating = rating
    if resolved_rating is None and "rating" in payload:
        try:
            resolved_rating = float(payload["rating"])
        except TypeError, ValueError:
            resolved_rating = None

    resolved_watched_at = watched_at
    if resolved_watched_at is None:
        for key in ("last_watched_at", "watched_at"):
            if raw := payload.get(key):
                parsed = parse_iso_datetime(str(raw))
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


def media_item_from_trakt_show(
    payload: dict[str, Any],
    *,
    source: str = "trakt",
    watchlisted: bool = False,
    rating: float | None = None,
) -> MediaItem | None:
    """Build a show ``MediaItem`` from a Trakt show object (watchlist)."""
    show = payload.get("show") if "show" in payload else payload
    if not isinstance(show, dict):
        return None

    ids = show.get("ids") or {}
    if not isinstance(ids, dict):
        return None
    identifiers = _trakt_ids(ids)
    if not identifiers:
        return None

    trakt_id = ids.get("trakt")
    source_key = f"trakt:show:{trakt_id}" if trakt_id is not None else ""

    resolved_rating = rating
    if resolved_rating is None and "rating" in payload:
        try:
            resolved_rating = float(payload["rating"])
        except TypeError, ValueError:
            resolved_rating = None

    return MediaItem(
        title=str(show.get("title") or "Unknown"),
        media_type=MediaType.SHOW,
        identifiers=identifiers,
        watchlisted=watchlisted,
        rating=resolved_rating,
        source=source,
        source_key=source_key,
    )


def media_item_from_trakt_episode(
    *,
    show: dict[str, Any],
    season: int,
    episode: int,
    watched_at: datetime | None = None,
    source: str = "trakt",
) -> MediaItem | None:
    """Build an episode ``MediaItem`` from Trakt show ids + season/episode."""
    ids = show.get("ids") or {}
    if not isinstance(ids, dict):
        return None
    identifiers = _trakt_ids(ids)
    if not identifiers:
        return None

    show_title = str(show.get("title") or "Unknown")
    trakt_id = ids.get("trakt")
    source_key = (
        f"trakt:show:{trakt_id}:s{season}e{episode}"
        if trakt_id is not None
        else f"trakt:{show_title}:s{season}e{episode}"
    )
    return MediaItem(
        title=format_episode_title(show_title, season, episode),
        media_type=MediaType.EPISODE,
        identifiers=identifiers,
        watched=True,
        watched_at=watched_at,
        source=source,
        source_key=source_key,
        season=season,
        episode=episode,
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
    """Alias for :func:`letterboxd_to_normalized` (Letterboxd 0.5–5 → 0–10)."""
    return letterboxd_to_normalized(stars)


def parse_letterboxd_rating(raw: str | None) -> float | None:
    if not raw:
        return None
    try:
        stars = float(raw)
    except ValueError:
        return None
    if stars <= 0:
        return None
    return letterboxd_to_normalized(stars)


def film_slug_from_url(url: str) -> str | None:
    return letterboxd_slug(url)
