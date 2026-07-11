"""TMDB API connection test."""

from __future__ import annotations

import httpx

from plextraktbox.clients.base import ConnectionTestResult

TMDB_BASE = "https://api.themoviedb.org/3"


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
