"""Letterboxd credential test and read-only fetch via official CSV export."""

from __future__ import annotations

import csv
import json
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from io import BytesIO, StringIO
from zipfile import ZipFile

import httpx

from plextraktbox.clients.base import ConnectionTestResult
from plextraktbox.clients.media_mappers import (
    media_item_from_letterboxd_film,
    parse_letterboxd_rating,
)
from plextraktbox.sync.guid import letterboxd_slug
from plextraktbox.sync.media_item import MediaItem

FilmResolver = Callable[[str, str, str | None], dict[str, str] | None]

LETTERBOXD_BASE = "https://letterboxd.com"
LOGIN_URL = f"{LETTERBOXD_BASE}/user/login.do"
EXPORT_URL = f"{LETTERBOXD_BASE}/data/export"
SIGNIN_URL = f"{LETTERBOXD_BASE}/sign-in/"
CSRF_COOKIE = "com.xk72.webparts.csrf"
USER_COOKIE = "letterboxd.signed.in.as"
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
}


@dataclass(frozen=True)
class LetterboxdExport:
    """Parsed CSV payloads from Letterboxd's official data export ZIP."""

    ratings_csv: str | None
    watchlist_csv: str | None
    diary_csv: str | None


def test_connection(username: str, password: str) -> ConnectionTestResult:
    try:
        with _authenticated_client(username, password) as _client:
            return ConnectionTestResult(
                ok=True,
                message="Letterboxd credentials accepted",
                details={"username": username},
            )
    except ValueError as exc:
        return ConnectionTestResult(ok=False, message=str(exc))
    except (httpx.HTTPError, ConnectionError) as exc:
        return ConnectionTestResult(ok=False, message=f"Letterboxd request failed: {exc}")


def download_export(username: str, password: str) -> LetterboxdExport:
    """Download and extract the official Letterboxd CSV export (ratings/watchlist/diary)."""
    with _authenticated_client(username, password) as client:
        resp = client.get(EXPORT_URL)
        content_type = resp.headers.get("content-type", "")
        if resp.status_code != 200 or "application/zip" not in content_type:
            raise ConnectionError(f"Failed to download Letterboxd export (HTTP {resp.status_code})")

        ratings_csv: str | None = None
        watchlist_csv: str | None = None
        diary_csv: str | None = None

        with ZipFile(BytesIO(resp.content)) as archive:
            for name in archive.namelist():
                if not name.endswith(".csv"):
                    continue
                payload = archive.read(name).decode("utf-8")
                basename = name.rsplit("/", 1)[-1].lower()
                if basename == "ratings.csv":
                    ratings_csv = payload
                elif basename == "watchlist.csv":
                    watchlist_csv = payload
                elif basename in {"diary.csv", "watched.csv"}:
                    diary_csv = payload

        return LetterboxdExport(
            ratings_csv=ratings_csv,
            watchlist_csv=watchlist_csv,
            diary_csv=diary_csv,
        )


def fetch_ratings_movies(
    username: str,
    password: str,
    *,
    resolve_identifiers: FilmResolver | None = None,
) -> list[MediaItem]:
    export = download_export(username, password)
    return items_from_ratings_csv(export.ratings_csv, resolve_identifiers=resolve_identifiers)


def fetch_watchlist_movies(
    username: str,
    password: str,
    *,
    resolve_identifiers: FilmResolver | None = None,
) -> list[MediaItem]:
    export = download_export(username, password)
    return items_from_watchlist_csv(export.watchlist_csv, resolve_identifiers=resolve_identifiers)


def fetch_watched_movies(
    username: str,
    password: str,
    *,
    resolve_identifiers: FilmResolver | None = None,
) -> list[MediaItem]:
    export = download_export(username, password)
    return items_from_diary_csv(export.diary_csv, resolve_identifiers=resolve_identifiers)


def items_from_ratings_csv(
    csv_text: str | None,
    *,
    resolve_identifiers: FilmResolver | None = None,
) -> list[MediaItem]:
    return _items_from_csv(
        csv_text,
        include_rating=True,
        resolve_identifiers=resolve_identifiers,
    )


def items_from_watchlist_csv(
    csv_text: str | None,
    *,
    resolve_identifiers: FilmResolver | None = None,
) -> list[MediaItem]:
    return _items_from_csv(
        csv_text,
        watchlisted=True,
        resolve_identifiers=resolve_identifiers,
    )


def items_from_diary_csv(
    csv_text: str | None,
    *,
    resolve_identifiers: FilmResolver | None = None,
) -> list[MediaItem]:
    return _items_from_csv(
        csv_text,
        include_watched=True,
        date_field="Watched Date",
        resolve_identifiers=resolve_identifiers,
    )


@contextmanager
def _authenticated_client(username: str, password: str) -> Iterator[httpx.Client]:
    client = httpx.Client(
        timeout=60.0,
        follow_redirects=True,
        headers=DEFAULT_HEADERS,
    )
    try:
        _login(client, username, password)
        yield client
    finally:
        client.close()


def _login(client: httpx.Client, username: str, password: str) -> None:
    home = client.get(LETTERBOXD_BASE)
    home.raise_for_status()

    csrf = client.cookies.get(CSRF_COOKIE)
    if not csrf:
        signin = client.get(SIGNIN_URL)
        signin.raise_for_status()
        csrf = client.cookies.get(CSRF_COOKIE)
    if not csrf:
        raise ValueError("Could not initialize Letterboxd sign-in session")

    resp = client.post(
        LOGIN_URL,
        data={
            "__csrf": csrf,
            "username": username,
            "password": password,
            "remember": "true",
        },
        headers={
            "Referer": SIGNIN_URL,
            "Origin": LETTERBOXD_BASE,
        },
    )

    content_type = resp.headers.get("content-type", "")
    if content_type.startswith("application/json"):
        try:
            payload = resp.json()
        except json.JSONDecodeError as exc:
            raise ValueError("Invalid Letterboxd login response") from exc
        if payload.get("result") != "success":
            raise ValueError("Invalid Letterboxd username or password")
        return

    if client.cookies.get(USER_COOKIE):
        return

    raise ValueError("Invalid Letterboxd username or password")


def _items_from_csv(
    csv_text: str | None,
    *,
    include_rating: bool = False,
    watchlisted: bool = False,
    include_watched: bool = False,
    date_field: str | None = None,
    resolve_identifiers: FilmResolver | None = None,
) -> list[MediaItem]:
    if not csv_text:
        return []

    items: list[MediaItem] = []
    seen: set[str] = set()
    reader = csv.DictReader(StringIO(csv_text))

    for row in reader:
        title = (row.get("Name") or "").strip()
        uri = (row.get("Letterboxd URI") or "").strip()
        if not title or not uri:
            continue

        slug = _slug_from_uri(uri)
        dedupe_key = slug or uri
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)

        identifiers: dict[str, str] = {}
        if resolve_identifiers is not None and slug is not None:
            year = (row.get("Year") or "").strip() or None
            identifiers = resolve_identifiers(slug, title, year) or {}

        rating = None
        if include_rating:
            rating = parse_letterboxd_rating(row.get("Rating"))

        watched_at = None
        if include_watched and date_field:
            watched_at = _parse_csv_date(row.get(date_field))

        items.append(
            media_item_from_letterboxd_film(
                title=title,
                slug=slug or dedupe_key,
                rating=rating,
                watchlisted=watchlisted,
                watched=include_watched,
                watched_at=watched_at,
                identifiers=identifiers,
            )
        )

    return items


def _slug_from_uri(uri: str) -> str | None:
    slug = letterboxd_slug(uri)
    if slug:
        return slug

    if "boxd.it" not in uri:
        return None

    try:
        resp = httpx.head(uri, follow_redirects=True, timeout=15.0, headers=DEFAULT_HEADERS)
        return letterboxd_slug(str(resp.url))
    except httpx.HTTPError:
        return None


def _parse_csv_date(raw: str | None) -> datetime | None:
    if not raw:
        return None
    try:
        parsed = datetime.strptime(raw.strip(), "%Y-%m-%d")
    except ValueError:
        return None
    return parsed.replace(tzinfo=UTC)
