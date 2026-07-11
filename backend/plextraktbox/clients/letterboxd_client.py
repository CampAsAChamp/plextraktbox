"""Letterboxd credential test (read-only scrape login)."""

from __future__ import annotations

import httpx

from plextraktbox.clients.base import ConnectionTestResult

LETTERBOXD_BASE = "https://letterboxd.com"
SIGNIN_URL = f"{LETTERBOXD_BASE}/sign-in/"
LOGIN_URL = f"{LETTERBOXD_BASE}/user/login.do"
CSRF_COOKIE = "com.xk72.webparts.csrf"
USER_COOKIE = "letterboxd.signed.in.as"
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
}


def test_connection(username: str, password: str) -> ConnectionTestResult:
    try:
        with httpx.Client(
            timeout=15.0,
            follow_redirects=False,
            headers=DEFAULT_HEADERS,
        ) as client:
            login_page = client.get(SIGNIN_URL)
            if login_page.status_code != 200:
                return ConnectionTestResult(
                    ok=False,
                    message=f"Could not reach Letterboxd (HTTP {login_page.status_code})",
                )

            csrf = client.cookies.get(CSRF_COOKIE)
            if not csrf:
                return ConnectionTestResult(
                    ok=False,
                    message="Could not initialize Letterboxd sign-in session",
                )

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

            if client.cookies.get(USER_COOKIE):
                return ConnectionTestResult(
                    ok=True,
                    message="Letterboxd credentials accepted",
                    details={"username": username},
                )

            # Successful login redirects away from sign-in.
            location = str(resp.headers.get("location", ""))
            if resp.status_code in {302, 303} and "sign-in" not in location:
                return ConnectionTestResult(
                    ok=True,
                    message="Letterboxd credentials accepted",
                    details={"username": username},
                )
    except httpx.HTTPError as exc:
        return ConnectionTestResult(ok=False, message=f"Letterboxd request failed: {exc}")

    return ConnectionTestResult(ok=False, message="Invalid Letterboxd username or password")
