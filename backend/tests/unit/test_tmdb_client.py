"""TMDB client tests."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from requests.exceptions import HTTPError

from plextraktbox.clients import tmdb_client


def test_resolve_letterboxd_film_prefers_tmdb_search(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    monkeypatch.setattr(
        tmdb_client,
        "search_movie_ids",
        lambda *_args, **_kwargs: calls.append("search") or {"tmdb": "603"},
    )
    monkeypatch.setattr(
        tmdb_client,
        "resolve_letterboxd_slug",
        lambda *_args, **_kwargs: calls.append("slug") or {},
    )

    ids = tmdb_client.resolve_letterboxd_film(
        "api-key",
        slug="the-matrix",
        title="The Matrix",
        year="1999",
    )

    assert ids == {"tmdb": "603"}
    assert calls == ["search"]


def test_resolve_letterboxd_film_falls_back_to_letterboxd_slug(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    monkeypatch.setattr(
        tmdb_client,
        "search_movie_ids",
        lambda *_args, **_kwargs: calls.append("search") or {},
    )
    monkeypatch.setattr(
        tmdb_client,
        "resolve_letterboxd_slug",
        lambda *_args, **_kwargs: calls.append("slug") or {"tmdb": "12345"},
    )

    ids = tmdb_client.resolve_letterboxd_film(
        "api-key",
        slug="obscure-film-2020",
        title="Obscure Film",
        year="2020",
    )

    assert ids == {"tmdb": "12345"}
    assert calls == ["search", "slug"]


def test_resolve_letterboxd_slug_treats_429_as_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(tmdb_client, "_throttle_letterboxd_fetch", lambda: None)

    def raise_429(*_args, **_kwargs) -> None:
        response = SimpleNamespace(status_code=429)
        raise HTTPError("429 Too Many Requests", response=response)

    monkeypatch.setattr(tmdb_client, "_fetch_letterboxd_film_page", raise_429)

    ids = tmdb_client.resolve_letterboxd_slug("api-key", "parasite-2019")

    assert ids == {}
