"""Trakt list TTL cache tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from plextraktbox.services import trakt_list_cache
from plextraktbox.sync.media_item import MediaItem, MediaType


def test_trakt_list_cache_hit_and_invalidate(client: TestClient) -> None:
    calls = 0

    def fetch() -> list[MediaItem]:
        nonlocal calls
        calls += 1
        return [
            MediaItem(
                title="The Matrix",
                media_type=MediaType.MOVIE,
                identifiers={"tmdb": "603"},
                watchlisted=True,
            )
        ]

    token = "trakt-token"
    first = trakt_list_cache.get_or_fetch_list(
        trakt_list_cache.LIST_WATCHLIST,
        token,
        ttl_minutes=30,
        force=False,
        fetch=fetch,
    )
    second = trakt_list_cache.get_or_fetch_list(
        trakt_list_cache.LIST_WATCHLIST,
        token,
        ttl_minutes=30,
        force=False,
        fetch=fetch,
    )
    assert calls == 1
    assert first[0].identifiers["tmdb"] == "603"
    assert second[0].title == "The Matrix"

    trakt_list_cache.invalidate_list(trakt_list_cache.LIST_WATCHLIST, token)
    third = trakt_list_cache.get_or_fetch_list(
        trakt_list_cache.LIST_WATCHLIST,
        token,
        ttl_minutes=30,
        force=False,
        fetch=fetch,
    )
    assert calls == 2
    assert len(third) == 1
