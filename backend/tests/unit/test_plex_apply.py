"""Plex apply client tests."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from plextraktbox.clients import plex_client
from plextraktbox.sync.media_item import MediaItem, MediaType


def _movie(*, tmdb: str = "603", title: str = "The Matrix") -> MediaItem:
    return MediaItem(
        title=title,
        media_type=MediaType.MOVIE,
        identifiers={"tmdb": tmdb},
    )


def _library_video(*, rating_key: str = "1", tmdb: str = "603", title: str = "The Matrix") -> SimpleNamespace:
    return SimpleNamespace(
        type="movie",
        title=title,
        ratingKey=rating_key,
        guid=f"tmdb://{tmdb}",
        guids=[],
        userRating=None,
        viewCount=0,
        lastViewedAt=None,
        isWatched=False,
    )


def test_rate_library_movies_calls_plex_rate(monkeypatch: pytest.MonkeyPatch) -> None:
    video = _library_video()
    rate_calls: list[float] = []
    video.rate = lambda rating: rate_calls.append(rating) or video  # type: ignore[method-assign]

    monkeypatch.setattr(
        plex_client,
        "_library_videos_by_match_key",
        lambda *_args, **_kwargs: {"tmdb:603": video},
    )

    plex_client.rate_library_movies(
        "http://plex.local:32400",
        "plex-token",
        [(_movie(), 9.0)],
    )

    assert rate_calls == [9.0]


def test_mark_library_movies_watched_skips_already_watched(monkeypatch: pytest.MonkeyPatch) -> None:
    video = _library_video()
    video.isWatched = True
    mark_calls = 0
    video.markWatched = lambda: nonlocal_mark()  # type: ignore[method-assign]

    def nonlocal_mark() -> None:
        nonlocal mark_calls
        mark_calls += 1

    monkeypatch.setattr(
        plex_client,
        "_library_videos_by_match_key",
        lambda *_args, **_kwargs: {"tmdb:603": video},
    )

    plex_client.mark_library_movies_watched(
        "http://plex.local:32400",
        "plex-token",
        [_movie()],
    )

    assert mark_calls == 0


def test_mark_library_movies_watched_marks_unwatched(monkeypatch: pytest.MonkeyPatch) -> None:
    video = _library_video()
    mark_calls = 0
    video.markWatched = lambda: nonlocal_mark()  # type: ignore[method-assign]

    def nonlocal_mark() -> None:
        nonlocal mark_calls
        mark_calls += 1

    monkeypatch.setattr(
        plex_client,
        "_library_videos_by_match_key",
        lambda *_args, **_kwargs: {"tmdb:603": video},
    )

    plex_client.mark_library_movies_watched(
        "http://plex.local:32400",
        "plex-token",
        [_movie()],
    )

    assert mark_calls == 1


def test_mark_library_items_watched_marks_episodes(monkeypatch: pytest.MonkeyPatch) -> None:
    episode_video = SimpleNamespace(isWatched=False)
    mark_calls = 0

    def nonlocal_mark() -> None:
        nonlocal mark_calls
        mark_calls += 1

    episode_video.markWatched = nonlocal_mark  # type: ignore[method-assign]

    monkeypatch.setattr(
        plex_client,
        "_library_videos_by_match_key",
        lambda *_args, **_kwargs: {},
    )
    monkeypatch.setattr(
        plex_client,
        "_library_episodes_by_match_key",
        lambda *_args, **_kwargs: {"tmdb:1396:s1e1": episode_video},
    )

    plex_client.mark_library_items_watched(
        "http://plex.local:32400",
        "plex-token",
        [
            MediaItem(
                title="Breaking Bad S01E01",
                media_type=MediaType.EPISODE,
                identifiers={"tmdb": "1396"},
                season=1,
                episode=1,
            )
        ],
    )

    assert mark_calls == 1


def test_add_watchlist_movies_skips_items_already_on_watchlist(monkeypatch: pytest.MonkeyPatch) -> None:
    discover_movie = SimpleNamespace(title="The Matrix", guid="tmdb://603")
    add_calls = 0
    account = SimpleNamespace(onWatchlist=lambda _item: True)

    def add_to_watchlist(_item: object) -> None:
        nonlocal add_calls
        add_calls += 1

    account.addToWatchlist = add_to_watchlist  # type: ignore[attr-defined]

    monkeypatch.setattr(plex_client, "_plex_account", lambda _token: account)
    monkeypatch.setattr(plex_client, "_resolve_discover_item", lambda _account, _item: discover_movie)

    plex_client.add_watchlist_movies("plex-token", [_movie()])

    assert add_calls == 0
