"""Letterboxd slug → identifiers cache tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from plextraktbox.services import letterboxd_slug_cache


def test_slug_cache_hit_skips_resolver(client: TestClient) -> None:
    calls = 0

    def resolver(slug: str, title: str, year: str | None = None) -> dict[str, str] | None:
        nonlocal calls
        calls += 1
        return {"tmdb": "42", "imdb": "tt1"}

    wrapped = letterboxd_slug_cache.wrap_resolver(resolver)
    first = wrapped("the-matrix", "The Matrix", "1999")
    second = wrapped("the-matrix", "The Matrix", "1999")

    assert first == {"tmdb": "42", "imdb": "tt1"}
    assert second == {"tmdb": "42", "imdb": "tt1"}
    assert calls == 1
    assert wrapped.stats()["hits"] == 1  # type: ignore[attr-defined]
    assert wrapped.stats()["newly_resolved"] == 1  # type: ignore[attr-defined]


def test_slug_cache_miss_is_negatively_cached(client: TestClient) -> None:
    calls = 0

    def resolver(slug: str, title: str, year: str | None = None) -> dict[str, str] | None:
        nonlocal calls
        calls += 1
        return None

    wrapped = letterboxd_slug_cache.wrap_resolver(resolver, miss_ttl_hours=1)
    assert wrapped("unknown", "Unknown") is None
    assert wrapped("unknown", "Unknown") is None
    assert calls == 1
