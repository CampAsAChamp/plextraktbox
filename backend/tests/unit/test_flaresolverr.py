"""Unit tests for FlareSolverr helper."""

from __future__ import annotations

import httpx
import pytest
import respx

from plextraktbox.clients import flaresolverr


@respx.mock
def test_create_session_returns_session_id() -> None:
    respx.post("http://fs.local/v1").mock(
        return_value=httpx.Response(200, json={"status": "ok", "session": "sess-1"})
    )
    assert flaresolverr.create_session("http://fs.local") == "sess-1"


@respx.mock
def test_request_get_returns_cookies_and_user_agent() -> None:
    respx.post("http://fs.local/v1").mock(
        return_value=httpx.Response(
            200,
            json={
                "status": "ok",
                "solution": {
                    "status": 200,
                    "userAgent": "Mozilla/5.0 TestAgent",
                    "cookies": [
                        {
                            "name": "com.xk72.webparts.csrf",
                            "value": "csrf-token",
                            "domain": ".letterboxd.com",
                            "path": "/",
                        }
                    ],
                },
            },
        )
    )
    solution = flaresolverr.request_get(
        "http://fs.local",
        "https://letterboxd.com",
        session_id="sess-1",
    )
    assert solution.user_agent == "Mozilla/5.0 TestAgent"
    assert solution.status == 200
    assert solution.cookies[0]["name"] == "com.xk72.webparts.csrf"


@respx.mock
def test_request_get_raises_on_flaresolverr_error() -> None:
    respx.post("http://fs.local/v1").mock(
        return_value=httpx.Response(
            200,
            json={"status": "error", "message": "Challenge timeout"},
        )
    )
    with pytest.raises(flaresolverr.FlareSolverrError, match="Challenge timeout"):
        flaresolverr.request_get("http://fs.local", "https://letterboxd.com")


@respx.mock
def test_destroy_session_swallows_errors() -> None:
    respx.post("http://fs.local/v1").mock(
        return_value=httpx.Response(200, json={"status": "error", "message": "gone"})
    )
    flaresolverr.destroy_session("http://fs.local", "sess-1")


def test_apply_cookies_sets_httpx_jar() -> None:
    client = httpx.Client()
    try:
        flaresolverr.apply_cookies(
            client,
            [
                {
                    "name": "com.xk72.webparts.csrf",
                    "value": "abc",
                    "domain": "letterboxd.com",
                    "path": "/",
                }
            ],
        )
        assert client.cookies.get("com.xk72.webparts.csrf") == "abc"
    finally:
        client.close()
