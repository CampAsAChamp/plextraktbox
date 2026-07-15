"""Plex Discover key cache tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from plextraktbox.services import plex_discover_key_cache
from plextraktbox.sync.media_item import MediaItem, MediaType


def test_discover_key_store_and_lookup(client: TestClient) -> None:
    item = MediaItem(
        title="The Matrix",
        media_type=MediaType.MOVIE,
        identifiers={"tmdb": "603", "imdb": "tt0133093"},
    )
    plex_discover_key_cache.store_discover_key(item, "abc123")
    assert plex_discover_key_cache.lookup_discover_key(item) == "abc123"

    plex_discover_key_cache.invalidate_discover_key(item)
    assert plex_discover_key_cache.lookup_discover_key(item) is None
