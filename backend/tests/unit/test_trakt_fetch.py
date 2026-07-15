"""Trakt fetch client tests (respx)."""

from __future__ import annotations

import respx
from httpx import Response

from plextraktbox.clients import trakt_client


@respx.mock
def test_fetch_watchlist_movies_maps_items() -> None:
    respx.get("https://api.trakt.tv/sync/watchlist").mock(
        return_value=Response(
            200,
            json=[
                {
                    "listed_at": "2024-01-01T00:00:00.000Z",
                    "type": "movie",
                    "movie": {
                        "title": "Parasite",
                        "year": 2019,
                        "ids": {
                            "trakt": 1,
                            "slug": "parasite-2019",
                            "imdb": "tt6751668",
                            "tmdb": 496243,
                        },
                    },
                }
            ],
        )
    )

    items = trakt_client.fetch_watchlist_movies("client-id", "access-token")
    assert len(items) == 1
    assert items[0].title == "Parasite"
    assert items[0].watchlisted is True
    assert items[0].identifiers["tmdb"] == "496243"


@respx.mock
def test_fetch_watchlist_shows_maps_items() -> None:
    respx.get("https://api.trakt.tv/sync/watchlist").mock(
        return_value=Response(
            200,
            json=[
                {
                    "listed_at": "2024-01-01T00:00:00.000Z",
                    "type": "show",
                    "show": {
                        "title": "Breaking Bad",
                        "year": 2008,
                        "ids": {
                            "trakt": 1,
                            "slug": "breaking-bad",
                            "tvdb": 81189,
                            "imdb": "tt0903747",
                            "tmdb": 1396,
                        },
                    },
                }
            ],
        )
    )

    items = trakt_client.fetch_watchlist_shows("client-id", "access-token")
    assert len(items) == 1
    assert items[0].title == "Breaking Bad"
    assert items[0].media_type.value == "show"
    assert items[0].identifiers["tmdb"] == "1396"


@respx.mock
def test_fetch_watched_episodes_expands_seasons() -> None:
    respx.get("https://api.trakt.tv/sync/watched/shows").mock(
        return_value=Response(
            200,
            json=[
                {
                    "plays": 2,
                    "last_watched_at": "2024-01-02T00:00:00.000Z",
                    "show": {
                        "title": "Breaking Bad",
                        "year": 2008,
                        "ids": {"trakt": 1, "tmdb": 1396, "tvdb": 81189, "imdb": "tt0903747"},
                    },
                    "seasons": [
                        {
                            "number": 1,
                            "episodes": [
                                {
                                    "number": 1,
                                    "plays": 1,
                                    "last_watched_at": "2024-01-01T00:00:00.000Z",
                                },
                                {
                                    "number": 2,
                                    "plays": 1,
                                    "last_watched_at": "2024-01-02T00:00:00.000Z",
                                },
                            ],
                        }
                    ],
                }
            ],
        )
    )

    items = trakt_client.fetch_watched_episodes("client-id", "access-token")
    assert len(items) == 2
    assert items[0].title == "Breaking Bad S01E01"
    assert items[0].match_key() == "tmdb:1396:s1e1"
    assert items[1].title == "Breaking Bad S01E02"
