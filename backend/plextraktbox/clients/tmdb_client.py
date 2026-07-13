"""TMDB API connection test and external-id lookup."""

from __future__ import annotations

import re

import httpx

from plextraktbox.clients.base import ConnectionTestResult
from plextraktbox.clients.http_cache import get_cached_requests_session

TMDB_BASE = "https://api.themoviedb.org/3"
LETTERBOXD_FILM_BASE = "https://letterboxd.com/film/"
_TMDB_ID_RE = re.compile(r'"tmdbId"\s*:\s*(\d+)')


def test_connection(api_key: str) -> ConnectionTestResult:
    try:
        resp = httpx.get(
            f"{TMDB_BASE}/configuration",
            params={"api_key": api_key},
            timeout=10.0,
        )
    except httpx.HTTPError as exc:
        return ConnectionTestResult(ok=False, message=f"TMDB request failed: {exc}")

    if resp.status_code == 401:
        return ConnectionTestResult(ok=False, message="Invalid TMDB API key")
    if resp.status_code != 200:
        return ConnectionTestResult(ok=False, message=f"TMDB returned HTTP {resp.status_code}")

    return ConnectionTestResult(ok=True, message="TMDB API key is valid")


def find_movie_ids(api_key: str, *, tmdb: str | None = None, imdb: str | None = None) -> dict[str, str]:
    """Resolve TMDB/IMDb ids via TMDB find API."""
    identifiers: dict[str, str] = {}
    if tmdb:
        identifiers["tmdb"] = str(tmdb)
    if imdb:
        identifiers["imdb"] = str(imdb)

    if tmdb or not imdb:
        return identifiers

    session = get_cached_requests_session()
    resp = session.get(
        f"{TMDB_BASE}/find/{imdb}",
        params={"api_key": api_key, "external_source": "imdb_id"},
        timeout=15.0,
    )
    if resp.status_code != 200:
        return identifiers

    data = resp.json()
    movie_results = data.get("movie_results") or []
    if not movie_results:
        return identifiers

    first = movie_results[0]
    if found_tmdb := first.get("id"):
        identifiers["tmdb"] = str(found_tmdb)
    return identifiers


def resolve_letterboxd_slug(api_key: str, slug: str) -> dict[str, str]:
    """Best-effort TMDB id lookup for a Letterboxd film slug."""
    session = get_cached_requests_session()
    resp = session.get(f"{LETTERBOXD_FILM_BASE}{slug}/", timeout=15.0)
    if resp.status_code != 200:
        return {}

    match = _TMDB_ID_RE.search(resp.text)
    if match:
        return {"tmdb": match.group(1)}

    # Fallback: TMDB search by title derived from slug (year suffix stripped)
    title = slug.rsplit("-", 1)[0].replace("-", " ")
    return search_movie_ids(api_key, title=title)


def search_movie_ids(
    api_key: str,
    *,
    title: str,
    year: str | int | None = None,
) -> dict[str, str]:
    """Resolve a movie title (and optional year) via TMDB search."""
    session = get_cached_requests_session()
    params: dict[str, str] = {"api_key": api_key, "query": title}
    if year not in (None, "", "0", 0):
        params["year"] = str(year)

    search = session.get(
        f"{TMDB_BASE}/search/movie",
        params=params,
        timeout=15.0,
    )
    if search.status_code != 200:
        return {}

    results = search.json().get("results") or []
    if not results:
        return {}

    return {"tmdb": str(results[0]["id"])}


def resolve_letterboxd_film(
    api_key: str,
    *,
    slug: str,
    title: str,
    year: str | int | None = None,
) -> dict[str, str]:
    """Resolve TMDB ids for a Letterboxd export row (slug first, then title/year)."""
    ids = resolve_letterboxd_slug(api_key, slug)
    if ids:
        return ids
    return search_movie_ids(api_key, title=title, year=year)
