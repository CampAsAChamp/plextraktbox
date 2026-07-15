"""Trakt apply client tests (respx)."""

from __future__ import annotations

import respx
from httpx import Response

from plextraktbox.clients import trakt_client
from plextraktbox.sync.media_item import MediaItem, MediaType


def _movie(*, tmdb: str = "603", title: str = "The Matrix") -> MediaItem:
    return MediaItem(
        title=title,
        media_type=MediaType.MOVIE,
        identifiers={"tmdb": tmdb},
    )


def _show(*, tmdb: str = "1396", title: str = "Breaking Bad") -> MediaItem:
    return MediaItem(
        title=title,
        media_type=MediaType.SHOW,
        identifiers={"tmdb": tmdb},
    )


@respx.mock
def test_add_watchlist_movies_posts_ids() -> None:
    route = respx.post("https://api.trakt.tv/sync/watchlist").mock(
        return_value=Response(200, json={"added": {"movies": 1}, "not_found": {"movies": []}})
    )

    trakt_client.add_watchlist_movies("client-id", "access-token", [_movie()])

    assert route.called
    assert route.calls.last.request.content == b'{"movies":[{"ids":{"tmdb":603}}]}'


@respx.mock
def test_add_watchlist_items_posts_movies_and_shows() -> None:
    route = respx.post("https://api.trakt.tv/sync/watchlist").mock(
        return_value=Response(
            200,
            json={
                "added": {"movies": 1, "shows": 1},
                "not_found": {"movies": [], "shows": []},
            },
        )
    )

    trakt_client.add_watchlist_items("client-id", "access-token", [_movie(), _show()])

    assert route.called
    body = route.calls.last.request.content.decode()
    assert '"movies":[{"ids":{"tmdb":603}}]' in body
    assert '"shows":[{"ids":{"tmdb":1396}}]' in body


@respx.mock
def test_add_watchlist_movies_raises_on_not_found() -> None:
    respx.post("https://api.trakt.tv/sync/watchlist").mock(
        return_value=Response(
            200,
            json={"added": {"movies": 0}, "not_found": {"movies": [{"ids": {"tmdb": 603}}]}},
        )
    )

    try:
        trakt_client.add_watchlist_movies("client-id", "access-token", [_movie()])
        raised = False
    except ValueError:
        raised = True

    assert raised


@respx.mock
def test_remove_watchlist_movies_posts_to_remove_endpoint() -> None:
    route = respx.post("https://api.trakt.tv/sync/watchlist/remove").mock(
        return_value=Response(200, json={"deleted": {"movies": 1}, "not_found": {"movies": []}})
    )

    trakt_client.remove_watchlist_movies("client-id", "access-token", [_movie()])

    assert route.called


@respx.mock
def test_remove_watchlist_movies_treats_not_found_as_idempotent() -> None:
    respx.post("https://api.trakt.tv/sync/watchlist/remove").mock(
        return_value=Response(
            200,
            json={"deleted": {"movies": 0}, "not_found": {"movies": [{"ids": {"tmdb": 603}}]}},
        )
    )

    trakt_client.remove_watchlist_movies("client-id", "access-token", [_movie()])


@respx.mock
def test_rate_movies_posts_ratings_payload() -> None:
    route = respx.post("https://api.trakt.tv/sync/ratings").mock(
        return_value=Response(200, json={"updated": {"movies": 1}, "not_found": {"movies": []}})
    )

    trakt_client.rate_movies("client-id", "access-token", [(_movie(), 9.0)])

    assert route.called
    body = route.calls.last.request.content.decode()
    assert '"rating":9.0' in body
    assert '"tmdb":603' in body


@respx.mock
def test_rate_movies_raises_on_not_found() -> None:
    respx.post("https://api.trakt.tv/sync/ratings").mock(
        return_value=Response(
            200,
            json={"updated": {"movies": 0}, "not_found": {"movies": [{"ids": {"tmdb": 603}}]}},
        )
    )

    try:
        trakt_client.rate_movies("client-id", "access-token", [(_movie(), 9.0)])
        raised = False
    except ValueError:
        raised = True

    assert raised
