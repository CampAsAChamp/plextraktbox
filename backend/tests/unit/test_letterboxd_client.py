"""Unit tests for Letterboxd CSV export parsing."""

from __future__ import annotations

import io
import zipfile

import httpx
import respx

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


def test_slug_from_uri_resolves_letterboxd_film_url() -> None:
    assert letterboxd_client._slug_from_uri("https://letterboxd.com/film/dune-2021/") == "dune-2021"
    assert (
        letterboxd_client._slug_from_uri("https://letterboxd.com/campasachamp/film/heat-1995/") == "heat-1995"
    )
