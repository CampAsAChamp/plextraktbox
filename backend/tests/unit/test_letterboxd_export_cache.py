"""Letterboxd export TTL file cache tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from plextraktbox.clients.letterboxd_client import LetterboxdExport
from plextraktbox.services import letterboxd_export_cache


def test_export_cache_hit_skips_download(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0

    def fake_download(
        username: str,
        password: str,
        *,
        flaresolverr_url: str | None = None,
        flaresolverr_timeout_ms: int | None = None,
    ) -> LetterboxdExport:
        nonlocal calls
        calls += 1
        return LetterboxdExport(
            ratings_csv="Name,Letterboxd URI\nFilm,https://letterboxd.com/film/x/\n",
            watchlist_csv=None,
            diary_csv=None,
        )

    monkeypatch.setattr(letterboxd_export_cache, "download_export", fake_download)

    first, status1 = letterboxd_export_cache.get_or_download_export(
        connection_id=1,
        username="user",
        password="pw",
        ttl_hours=24,
    )
    second, status2 = letterboxd_export_cache.get_or_download_export(
        connection_id=1,
        username="user",
        password="pw",
        ttl_hours=24,
    )

    assert status1 == "miss"
    assert status2 == "hit"
    assert calls == 1
    assert first.ratings_csv == second.ratings_csv


def test_export_cache_force_and_invalidate(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0

    def fake_download(
        username: str,
        password: str,
        *,
        flaresolverr_url: str | None = None,
        flaresolverr_timeout_ms: int | None = None,
    ) -> LetterboxdExport:
        nonlocal calls
        calls += 1
        return LetterboxdExport(ratings_csv=f"call,{calls}", watchlist_csv=None, diary_csv=None)

    monkeypatch.setattr(letterboxd_export_cache, "download_export", fake_download)

    letterboxd_export_cache.get_or_download_export(
        connection_id=2,
        username="user",
        password="pw",
        ttl_hours=24,
    )
    forced, status = letterboxd_export_cache.get_or_download_export(
        connection_id=2,
        username="user",
        password="pw",
        ttl_hours=24,
        force=True,
    )
    assert status == "forced"
    assert calls == 2
    assert forced.ratings_csv == "call,2"

    assert letterboxd_export_cache.invalidate_export_cache(2) is True
    _, status3 = letterboxd_export_cache.get_or_download_export(
        connection_id=2,
        username="user",
        password="pw",
        ttl_hours=24,
    )
    assert status3 == "miss"
    assert calls == 3
