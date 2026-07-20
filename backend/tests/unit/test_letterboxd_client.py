"""Unit tests for Letterboxd CSV export parsing."""

from __future__ import annotations

import io
import json
import zipfile

import httpx
import pytest
import respx

from plextraktbox import config
from plextraktbox.clients import letterboxd_client

RATINGS_CSV = """Date,Name,Year,Letterboxd URI,Rating
2024-01-01,Dune,2021,https://letterboxd.com/film/dune-2021/,4.5
2024-01-02,Barbie,2023,https://letterboxd.com/film/barbie/,5
"""

WATCHLIST_CSV = """Name,Year,Letterboxd URI,Date Added
Heat,1995,https://letterboxd.com/film/heat-1995/,2024-01-01
"""

DIARY_CSV = """Watched Date,Name,Year,Letterboxd URI,Rating,Rewatch,Tags
2024-06-01,Arrival,2016,https://letterboxd.com/film/arrival/,3.5,No,
"""


def _zip_bytes(*files: tuple[str, str]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for name, content in files:
            archive.writestr(name, content)
    return buffer.getvalue()


def test_items_from_ratings_csv_maps_ratings() -> None:
    items = letterboxd_client.items_from_ratings_csv(
        RATINGS_CSV,
        resolve_identifiers=lambda slug, title, year: {"tmdb": "603"} if slug == "dune-2021" else None,
    )
    assert len(items) == 2
    assert items[0].title == "Dune"
    assert items[0].rating == 9.0
    assert items[0].identifiers == {"tmdb": "603"}
    assert items[1].title == "Barbie"
    assert items[1].rating == 10.0


def test_items_from_watchlist_csv_marks_watchlisted() -> None:
    items = letterboxd_client.items_from_watchlist_csv(WATCHLIST_CSV)
    assert len(items) == 1
    assert items[0].title == "Heat"
    assert items[0].watchlisted is True


def test_items_from_diary_csv_marks_watched() -> None:
    items = letterboxd_client.items_from_diary_csv(DIARY_CSV)
    assert len(items) == 1
    assert items[0].title == "Arrival"
    assert items[0].watched is True
    assert items[0].watched_at is not None
    assert items[0].watched_at.year == 2024


@respx.mock
def test_download_export_parses_zip_payload() -> None:
    respx.get("https://letterboxd.com/").mock(
        return_value=httpx.Response(
            200,
            headers={"set-cookie": "com.xk72.webparts.csrf=test-csrf; Path=/"},
        )
    )
    respx.post("https://letterboxd.com/user/login.do").mock(
        return_value=httpx.Response(
            200,
            json={"result": "success"},
            headers={"content-type": "application/json"},
        )
    )
    respx.get("https://letterboxd.com/data/export").mock(
        return_value=httpx.Response(
            200,
            content=_zip_bytes(
                ("ratings.csv", RATINGS_CSV),
                ("watchlist.csv", WATCHLIST_CSV),
                ("diary.csv", DIARY_CSV),
            ),
            headers={"content-type": "application/zip"},
        )
    )

    export = letterboxd_client.download_export("nick", "secret")
    assert export.ratings_csv is not None
    assert export.watchlist_csv is not None
    assert export.diary_csv is not None
    assert len(letterboxd_client.items_from_ratings_csv(export.ratings_csv)) == 2


@respx.mock
def test_test_connection_accepts_json_login() -> None:
    respx.get("https://letterboxd.com/").mock(
        return_value=httpx.Response(
            200,
            headers={"set-cookie": "com.xk72.webparts.csrf=test-csrf; Path=/"},
        )
    )
    respx.post("https://letterboxd.com/user/login.do").mock(
        return_value=httpx.Response(
            200,
            json={"result": "success"},
            headers={"content-type": "application/json"},
        )
    )

    result = letterboxd_client.test_connection("nick", "secret")
    assert result.ok is True


@respx.mock
def test_test_connection_hints_flaresolverr_on_cloudflare_403(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("FLARESOLVERR_URL", raising=False)
    config.get_settings.cache_clear()
    respx.get("https://letterboxd.com/").mock(
        return_value=httpx.Response(
            403,
            headers={"cf-mitigated": "challenge"},
            text="<html><title>Just a moment...</title></html>",
        )
    )

    result = letterboxd_client.test_connection("nick", "secret")
    assert result.ok is False
    assert "FLARESOLVERR_URL" in result.message or "FlareSolverr" in result.message
    assert "Connections" in result.message
    config.get_settings.cache_clear()


@respx.mock
def test_test_connection_bootstraps_via_flaresolverr(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FLARESOLVERR_URL", "http://fs.local")
    config.get_settings.cache_clear()

    def _fs_handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        cmd = payload.get("cmd")
        if cmd == "sessions.create":
            return httpx.Response(200, json={"status": "ok", "session": "sess-1"})
        if cmd == "sessions.destroy":
            return httpx.Response(200, json={"status": "ok"})
        if cmd == "request.get":
            return httpx.Response(
                200,
                json={
                    "status": "ok",
                    "solution": {
                        "status": 200,
                        "userAgent": "Mozilla/5.0 FS-Agent",
                        "cookies": [
                            {
                                "name": "com.xk72.webparts.csrf",
                                "value": "fs-csrf",
                                "domain": "letterboxd.com",
                                "path": "/",
                            },
                            {
                                "name": "cf_clearance",
                                "value": "cleared",
                                "domain": ".letterboxd.com",
                                "path": "/",
                            },
                        ],
                    },
                },
            )
        return httpx.Response(500, json={"status": "error", "message": f"unexpected {cmd}"})

    respx.post("http://fs.local/v1").mock(side_effect=_fs_handler)
    login_route = respx.post("https://letterboxd.com/user/login.do").mock(
        return_value=httpx.Response(
            200,
            json={"result": "success"},
            headers={"content-type": "application/json"},
        )
    )

    result = letterboxd_client.test_connection("nick", "secret")
    assert result.ok is True
    assert login_route.called
    assert b"fs-csrf" in login_route.calls[0].request.content

    monkeypatch.delenv("FLARESOLVERR_URL", raising=False)
    config.get_settings.cache_clear()


@respx.mock
def test_test_connection_connection_url_overrides_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FLARESOLVERR_URL", "http://env-fs.local")
    config.get_settings.cache_clear()

    def _fs_handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        cmd = payload.get("cmd")
        if cmd == "sessions.create":
            return httpx.Response(200, json={"status": "ok", "session": "sess-1"})
        if cmd == "sessions.destroy":
            return httpx.Response(200, json={"status": "ok"})
        if cmd == "request.get":
            return httpx.Response(
                200,
                json={
                    "status": "ok",
                    "solution": {
                        "status": 200,
                        "userAgent": "Mozilla/5.0 FS-Agent",
                        "cookies": [
                            {
                                "name": "com.xk72.webparts.csrf",
                                "value": "fs-csrf",
                                "domain": "letterboxd.com",
                                "path": "/",
                            }
                        ],
                    },
                },
            )
        return httpx.Response(500, json={"status": "error", "message": f"unexpected {cmd}"})

    env_route = respx.post("http://env-fs.local/v1").mock(side_effect=_fs_handler)
    ui_route = respx.post("http://ui-fs.local/v1").mock(side_effect=_fs_handler)
    respx.post("https://letterboxd.com/user/login.do").mock(
        return_value=httpx.Response(
            200,
            json={"result": "success"},
            headers={"content-type": "application/json"},
        )
    )

    result = letterboxd_client.test_connection(
        "nick",
        "secret",
        flaresolverr_url="http://ui-fs.local",
        flaresolverr_timeout_ms=45_000,
    )
    assert result.ok is True
    assert ui_route.called
    assert not env_route.called

    monkeypatch.delenv("FLARESOLVERR_URL", raising=False)
    config.get_settings.cache_clear()


def test_resolve_flaresolverr_prefers_connection_over_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FLARESOLVERR_URL", "http://env-fs.local")
    monkeypatch.setenv("FLARESOLVERR_TIMEOUT_MS", "12000")
    config.get_settings.cache_clear()

    url, timeout = letterboxd_client.resolve_flaresolverr(
        flaresolverr_url="http://ui-fs.local/",
        flaresolverr_timeout_ms=45_000,
    )
    assert url == "http://ui-fs.local"
    assert timeout == 45_000

    url_env, timeout_env = letterboxd_client.resolve_flaresolverr()
    assert url_env == "http://env-fs.local"
    assert timeout_env == 12_000

    monkeypatch.delenv("FLARESOLVERR_URL", raising=False)
    monkeypatch.delenv("FLARESOLVERR_TIMEOUT_MS", raising=False)
    config.get_settings.cache_clear()


def test_slug_from_uri_resolves_letterboxd_film_url() -> None:
    assert letterboxd_client._slug_from_uri("https://letterboxd.com/film/dune-2021/") == "dune-2021"
    assert (
        letterboxd_client._slug_from_uri("https://letterboxd.com/campasachamp/film/heat-1995/") == "heat-1995"
    )
