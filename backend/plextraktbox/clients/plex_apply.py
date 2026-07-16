"""Plex apply operations: ratings, watched state, and watchlist changes."""

from __future__ import annotations

from typing import Any

import httpx
from plexapi.myplex import MyPlexAccount

from plextraktbox.clients.http_cache import get_cached_requests_session
from plextraktbox.clients.plex_library import PlexLibrarySnapshot
from plextraktbox.sync.media_item import MediaItem, MediaType


def _log():
    from plextraktbox.logging_setup import get_logger

    return get_logger(__name__)


PLEX_DISCOVER_BASE = "https://discover.provider.plex.tv"
PLEX_DISCOVER_IDENTIFIER = "tv.plex.provider.discover"


def rate_library_movies(
    url: str,
    token: str,
    ratings: list[tuple[MediaItem, float]],
    *,
    library_ids: list[str] | None = None,
    snapshot: PlexLibrarySnapshot | None = None,
) -> None:
    """Apply user ratings to movies in scoped Plex libraries."""
    from plextraktbox.clients import plex_client

    if not ratings:
        return
    index = plex_client._library_videos_by_match_key(url, token, library_ids=library_ids, snapshot=snapshot)
    for item, rating in ratings:
        video = plex_client._find_library_video(index, item)
        video.rate(rating)


def _discover_metadata_key(video: Any) -> str:
    """Extract the Plex Discover metadata key from a discover ``Movie`` object."""
    guid = str(getattr(video, "guid", "") or "")
    if guid.startswith("plex://movie/"):
        return guid.rsplit("/", 1)[-1]

    rating_key = getattr(video, "ratingKey", None)
    if rating_key is not None and str(rating_key).lower() not in {"", "nan", "none"}:
        return str(rating_key)

    key = str(getattr(video, "key", "") or "")
    if "/library/metadata/" in key:
        return key.rsplit("/", 1)[-1]

    raise ValueError(f"Could not resolve Plex Discover key for {getattr(video, 'title', 'movie')!r}")


def rate_discover_movie(token: str, item: MediaItem, rating: float) -> None:
    """Rate a movie via Plex Discover (no local library copy required)."""
    from plextraktbox.clients import plex_client
    from plextraktbox.services import plex_discover_key_cache

    cached_key = plex_discover_key_cache.lookup_discover_key(item)
    if cached_key is not None:
        try:
            rate_discover_movie_by_key(token, cached_key, rating)
            return
        except Exception:
            plex_discover_key_cache.invalidate_discover_key(item)

    account = plex_client._plex_account(token)
    movie = plex_client._resolve_discover_movie(account, item)
    discover_key = _discover_metadata_key(movie)
    plex_discover_key_cache.store_discover_key(item, discover_key)
    try:
        rate_discover_movie_by_key(token, discover_key, rating)
    except Exception:
        plex_discover_key_cache.invalidate_discover_key(item)
        raise


def rate_discover_movie_by_key(token: str, discover_key: str, rating: float) -> None:
    """Rate a Plex Discover movie by metadata key (0–10 scale; -1 clears)."""
    if not (-1 <= rating <= 10):
        raise ValueError("Plex Discover rating must be between 0 and 10, or -1 to clear")
    resp = httpx.put(
        f"{PLEX_DISCOVER_BASE}/actions/rate",
        headers={"X-Plex-Token": token, "Accept": "application/json"},
        params={
            "identifier": PLEX_DISCOVER_IDENTIFIER,
            "key": discover_key,
            "rating": rating,
        },
        timeout=15.0,
    )
    resp.raise_for_status()


def rate_movies_with_discover_fallback(
    url: str,
    token: str,
    ratings: list[tuple[MediaItem, float]],
    *,
    library_ids: list[str] | None = None,
    snapshot: PlexLibrarySnapshot | None = None,
) -> tuple[int, int, int]:
    """Rate movies in-library when possible; otherwise fall back to Plex Discover.

    Returns ``(library_applied, discover_applied, errors)``. One failed movie does
    not abort the rest of the batch.
    """
    from plextraktbox.clients import plex_client

    if not ratings:
        return 0, 0, 0

    _log().info(
        "sync.apply.plex.index.start",
        message=(f"Indexing scoped Plex library before applying {len(ratings)} rating(s)"),
        count=len(ratings),
    )
    index = plex_client._library_videos_by_match_key(url, token, library_ids=library_ids, snapshot=snapshot)
    _log().info(
        "sync.apply.plex.index.done",
        message=(f"Indexed {len(index)} library movie(s); applying {len(ratings)} rating(s)"),
        library_count=len(index),
        count=len(ratings),
    )

    library_applied = 0
    discover_applied = 0
    errors = 0

    for item, rating in ratings:
        try:
            match_key = item.match_key()
            if match_key and match_key in index:
                index[match_key].rate(rating)
                library_applied += 1
                _log().info(
                    "sync.apply.plex.rate",
                    message=f'rated "{item.title}" on plex via library',
                    title=item.title,
                    rating=rating,
                    via="library",
                )
                continue
            _log().info(
                "sync.apply.plex.discover",
                message=f'resolving "{item.title}" on Plex Discover',
                title=item.title,
                rating=rating,
            )
            plex_client.rate_discover_movie(token, item, rating)
            discover_applied += 1
            _log().info(
                "sync.apply.plex.rate",
                message=f'rated "{item.title}" on plex via Discover',
                title=item.title,
                rating=rating,
                via="discover",
            )
        except Exception as exc:
            errors += 1
            _log().warning(
                "sync.apply.plex.rate.failed",
                message=f'Failed to rate "{item.title}" on plex: {exc}',
                title=item.title,
                rating=rating,
                error=str(exc),
            )

    error_suffix = f", {errors} failed" if errors else ""
    _log().info(
        "sync.apply.plex.rate.done",
        message=(
            f"Plex ratings complete: {library_applied} via library, "
            f"{discover_applied} via Discover{error_suffix}"
        ),
        library_applied=library_applied,
        discover_applied=discover_applied,
        errors=errors,
    )
    return library_applied, discover_applied, errors


def mark_library_movies_watched(
    url: str,
    token: str,
    items: list[MediaItem],
    *,
    library_ids: list[str] | None = None,
    snapshot: PlexLibrarySnapshot | None = None,
) -> None:
    """Mark movies as watched in scoped Plex libraries."""
    from plextraktbox.clients import plex_client

    movies = [item for item in items if item.media_type == MediaType.MOVIE]
    if not movies:
        return
    index = plex_client._library_videos_by_match_key(url, token, library_ids=library_ids, snapshot=snapshot)
    for item in movies:
        video = plex_client._find_library_video(index, item)
        if not video.isWatched:
            video.markWatched()


def mark_library_items_watched(
    url: str,
    token: str,
    items: list[MediaItem],
    *,
    library_ids: list[str] | None = None,
    snapshot: PlexLibrarySnapshot | None = None,
) -> None:
    """Mark movies and episodes as watched in scoped Plex libraries."""
    from plextraktbox.clients import plex_client

    if not items:
        return
    movies = [item for item in items if item.media_type == MediaType.MOVIE]
    episodes = [item for item in items if item.media_type == MediaType.EPISODE]
    if movies:
        mark_library_movies_watched(url, token, movies, library_ids=library_ids, snapshot=snapshot)
    if not episodes:
        return
    index = plex_client._library_episodes_by_match_key(url, token, library_ids=library_ids, snapshot=snapshot)
    for item in episodes:
        video = plex_client._find_library_video(index, item)
        if not video.isWatched:
            video.markWatched()


def _plex_account(token: str) -> MyPlexAccount:
    session = get_cached_requests_session()
    return MyPlexAccount(token=token, session=session)


def _resolve_discover_item(account: MyPlexAccount, item: MediaItem) -> Any:
    """Resolve a Plex Discover movie or show object for watchlist writes."""
    from plextraktbox.clients.media_mappers import media_item_from_plex_video
    from plextraktbox.services import plex_discover_key_cache

    libtype = "show" if item.media_type == MediaType.SHOW else "movie"
    target_key = item.match_key()
    results = account.searchDiscover(item.title, limit=25, libtype=libtype)
    for result in results:
        mapped = media_item_from_plex_video(result)
        if mapped is None:
            continue
        if target_key and mapped.match_key() == target_key:
            try:
                discover_key = _discover_metadata_key(result)
            except ValueError:
                return result
            plex_discover_key_cache.store_discover_key(item, discover_key)
            return result
    plex_discover_key_cache.invalidate_discover_key(item)
    raise ValueError(f"Could not resolve {item.title!r} on Plex Discover")


def _resolve_discover_movie(account: MyPlexAccount, item: MediaItem) -> Any:
    """Resolve a Plex Discover movie object for watchlist writes."""
    return _resolve_discover_item(account, item)


def _find_watchlist_entry(account: MyPlexAccount, item: MediaItem) -> Any:
    from plextraktbox.clients.media_mappers import media_item_from_plex_video

    target_key = item.match_key()
    allowed = {"show"} if item.media_type == MediaType.SHOW else {"movie"}
    for entry in account.watchlist():
        if str(getattr(entry, "type", "")).lower() not in allowed:
            continue
        mapped = media_item_from_plex_video(entry)
        if mapped is not None and target_key and mapped.match_key() == target_key:
            return entry
    raise ValueError(f"{item.title!r} is not on the Plex watchlist")


def add_watchlist_movies(token: str, items: list[MediaItem]) -> None:
    """Add movies to the Plex account watchlist via Discover."""
    add_watchlist_items(token, [item for item in items if item.media_type == MediaType.MOVIE])


def add_watchlist_items(token: str, items: list[MediaItem]) -> None:
    """Add movies and shows to the Plex account watchlist via Discover."""
    from plextraktbox.clients import plex_client

    if not items:
        return
    account = plex_client._plex_account(token)
    for item in items:
        if item.media_type not in {MediaType.MOVIE, MediaType.SHOW}:
            continue
        discover_item = plex_client._resolve_discover_item(account, item)
        if account.onWatchlist(discover_item):
            continue
        account.addToWatchlist(discover_item)


def remove_watchlist_movies(token: str, items: list[MediaItem]) -> None:
    """Remove movies from the Plex account watchlist."""
    remove_watchlist_items(token, [item for item in items if item.media_type == MediaType.MOVIE])


def remove_watchlist_items(token: str, items: list[MediaItem]) -> None:
    """Remove movies and shows from the Plex account watchlist."""
    from plextraktbox.clients import plex_client

    if not items:
        return
    account = plex_client._plex_account(token)
    for item in items:
        if item.media_type not in {MediaType.MOVIE, MediaType.SHOW}:
            continue
        try:
            entry = plex_client._find_watchlist_entry(account, item)
        except ValueError:
            continue
        if account.onWatchlist(entry):
            account.removeFromWatchlist(entry)
