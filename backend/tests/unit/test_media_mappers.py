"""Tests for API payload → MediaItem mappers."""

from __future__ import annotations

from types import SimpleNamespace

from plextraktbox.clients.media_mappers import (
    media_item_from_plex_episode,
    media_item_from_plex_video,
    media_item_from_trakt_episode,
    media_item_from_trakt_movie,
    media_item_from_trakt_show,
    parse_letterboxd_rating,
)
from plextraktbox.sync.media_item import MediaType


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


def test_trakt_show_watchlist_mapping() -> None:
    item = media_item_from_trakt_show(
        {
            "listed_at": "2024-01-01T00:00:00.000Z",
            "type": "show",
            "show": {
                "title": "Breaking Bad",
                "year": 2008,
                "ids": {"trakt": 1, "tmdb": 1396, "tvdb": 81189, "imdb": "tt0903747"},
            },
        },
        watchlisted=True,
    )
    assert item is not None
    assert item.media_type == MediaType.SHOW
    assert item.title == "Breaking Bad"
    assert item.identifiers["tmdb"] == "1396"
    assert item.match_key() == "tmdb:1396"


def test_trakt_episode_mapping() -> None:
    item = media_item_from_trakt_episode(
        show={
            "title": "Breaking Bad",
            "ids": {"trakt": 1, "tmdb": 1396, "tvdb": 81189},
        },
        season=1,
        episode=1,
    )
    assert item is not None
    assert item.media_type == MediaType.EPISODE
    assert item.title == "Breaking Bad S01E01"
    assert item.season == 1
    assert item.episode == 1
    assert item.match_key() == "tmdb:1396:s1e1"
    assert item.watched is True


def test_plex_show_mapping() -> None:
    video = SimpleNamespace(
        type="show",
        title="Breaking Bad",
        ratingKey="10",
        guid="tmdb://1396",
        guids=[SimpleNamespace(id="tmdb://1396")],
        userRating=None,
        viewCount=0,
        lastViewedAt=None,
    )
    item = media_item_from_plex_video(video)
    assert item is not None
    assert item.media_type == MediaType.SHOW
    assert item.identifiers["tmdb"] == "1396"


def test_plex_episode_mapping_uses_show_ids() -> None:
    video = SimpleNamespace(
        type="episode",
        title="Pilot",
        parentIndex=1,
        index=1,
        grandparentTitle="Breaking Bad",
        ratingKey="11",
        guid="plex://episode/1",
        guids=[],
        userRating=None,
        viewCount=1,
        lastViewedAt=None,
    )
    item = media_item_from_plex_episode(
        video,
        show_identifiers={"tmdb": "1396"},
        show_title="Breaking Bad",
    )
    assert item is not None
    assert item.media_type == MediaType.EPISODE
    assert item.title == "Breaking Bad S01E01"
    assert item.match_key() == "tmdb:1396:s1e1"
    assert item.watched is True


def test_letterboxd_rating_normalization() -> None:
    assert parse_letterboxd_rating("4.5") == 9.0
    assert parse_letterboxd_rating(None) is None
