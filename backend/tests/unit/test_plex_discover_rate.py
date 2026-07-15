"""Plex Discover rating tests (respx)."""

from __future__ import annotations

import httpx
import pytest
import respx

from plextraktbox.clients import plex_client
from plextraktbox.sync.media_item import MediaItem, MediaType


@respx.mock
def test_rate_discover_movie_by_key_puts_discover_endpoint() -> None:
    route = respx.put("https://discover.provider.plex.tv/actions/rate").mock(
        return_value=httpx.Response(200, text="")
    )

    plex_client.rate_discover_movie_by_key("plex-token", "5d7768244de0ee001fcc7fed", 9.0)

    assert route.called
    request = route.calls.last.request
    assert request.headers["X-Plex-Token"] == "plex-token"
    assert "identifier=tv.plex.provider.discover" in str(request.url)
    assert "key=5d7768244de0ee001fcc7fed" in str(request.url)
    assert "rating=9.0" in str(request.url)


def test_discover_metadata_key_from_guid() -> None:
    video = type(
        "Video",
        (),
        {"guid": "plex://movie/5d7768244de0ee001fcc7fed", "title": "The Social Network"},
    )()
    assert plex_client._discover_metadata_key(video) == "5d7768244de0ee001fcc7fed"


def test_rate_movies_with_discover_fallback_uses_discover_when_not_in_library(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from structlog.testing import capture_logs

    item = MediaItem(
        title="The Social Network",
        media_type=MediaType.MOVIE,
        identifiers={"tmdb": "37799"},
    )
    discover_calls: list[float] = []

    monkeypatch.setattr(plex_client, "_library_videos_by_match_key", lambda *_a, **_k: {})
    monkeypatch.setattr(
        plex_client,
        "rate_discover_movie",
        lambda _token, _item, rating: discover_calls.append(rating),
    )

    with capture_logs() as logs:
        library_count, discover_count, errors = plex_client.rate_movies_with_discover_fallback(
            "http://plex.local:32400",
            "plex-token",
            [(item, 9.0)],
        )

    assert library_count == 0
    assert discover_count == 1
    assert errors == 0
    assert discover_calls == [9.0]
    events = [entry["event"] for entry in logs]
    assert "sync.apply.plex.index.start" in events
    assert "sync.apply.plex.discover" in events
    assert "sync.apply.plex.rate" in events
    assert "sync.apply.plex.rate.done" in events


def test_rate_movies_with_discover_fallback_logs_per_item_failures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from structlog.testing import capture_logs

    good = MediaItem(
        title="Good Film",
        media_type=MediaType.MOVIE,
        identifiers={"tmdb": "1"},
    )
    bad = MediaItem(
        title="Bad Film",
        media_type=MediaType.MOVIE,
        identifiers={"tmdb": "2"},
    )

    monkeypatch.setattr(plex_client, "_library_videos_by_match_key", lambda *_a, **_k: {})

    def rate_discover(_token: str, item: MediaItem, rating: float) -> None:
        if item.title == "Bad Film":
            raise ValueError("Could not resolve on Discover")

    monkeypatch.setattr(plex_client, "rate_discover_movie", rate_discover)

    with capture_logs() as logs:
        library_count, discover_count, errors = plex_client.rate_movies_with_discover_fallback(
            "http://plex.local:32400",
            "plex-token",
            [(good, 8.0), (bad, 9.0)],
        )

    assert library_count == 0
    assert discover_count == 1
    assert errors == 1
    failed = next(entry for entry in logs if entry["event"] == "sync.apply.plex.rate.failed")
    assert failed["title"] == "Bad Film"
    assert 'Failed to rate "Bad Film"' in failed["message"]
