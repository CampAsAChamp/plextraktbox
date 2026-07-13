"""Tests for API payload → MediaItem mappers."""

from __future__ import annotations

from plextraktbox.clients.media_mappers import (
    media_item_from_trakt_movie,
    parse_letterboxd_rating,
)


def test_trakt_watchlist_movie_mapping() -> None:
    item = media_item_from_trakt_movie(
        {
            "listed_at": "2024-01-01T00:00:00.000Z",
            "type": "movie",
            "movie": {
                "title": "Parasite",
                "year": 2019,
                "ids": {"trakt": 1, "slug": "parasite-2019", "imdb": "tt6751668", "tmdb": 496243},
            },
        },
        watchlisted=True,
    )
    assert item is not None
    assert item.title == "Parasite"
    assert item.watchlisted is True
    assert item.identifiers["tmdb"] == "496243"
    assert item.identifiers["imdb"] == "tt6751668"
    assert item.source_key == "trakt:1"


def test_trakt_ratings_movie_mapping() -> None:
    item = media_item_from_trakt_movie(
        {
            "rated_at": "2024-01-01T00:00:00.000Z",
            "rating": 9.0,
            "type": "movie",
            "movie": {
                "title": "Parasite",
                "year": 2019,
                "ids": {"trakt": 1, "slug": "parasite-2019", "imdb": "tt6751668", "tmdb": 496243},
            },
        }
    )
    assert item is not None
    assert item.rating == 9.0


def test_letterboxd_rating_normalization() -> None:
    assert parse_letterboxd_rating("4.5") == 9.0
    assert parse_letterboxd_rating(None) is None
