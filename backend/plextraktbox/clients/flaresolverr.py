"""Minimal FlareSolverr client for Cloudflare challenge bootstrap."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from urllib.parse import urljoin

import httpx


@dataclass(frozen=True)
class FlareSolverrSolution:
    """Cookies and User-Agent returned after a successful FlareSolverr request."""

    cookies: list[dict[str, Any]]
    user_agent: str
    status: int


class FlareSolverrError(ConnectionError):
    """FlareSolverr request failed or returned a non-ok status."""


def create_session(base_url: str, *, timeout_ms: int = 60_000) -> str:
    """Create a persistent FlareSolverr browser session. Returns the session id."""
    payload = _post(base_url, {"cmd": "sessions.create"}, timeout_ms=timeout_ms)
    session_id = payload.get("session")
    if not isinstance(session_id, str) or not session_id:
        raise FlareSolverrError("FlareSolverr sessions.create did not return a session id")
    return session_id


def destroy_session(base_url: str, session_id: str, *, timeout_ms: int = 60_000) -> None:
    """Destroy a FlareSolverr browser session (best-effort)."""
    try:
        _post(
            base_url,
            {"cmd": "sessions.destroy", "session": session_id},
            timeout_ms=timeout_ms,
        )
    except FlareSolverrError:
        # Cleanup should not mask the original Letterboxd failure.
        return


def request_get(
    base_url: str,
    url: str,
    *,
    session_id: str | None = None,
    timeout_ms: int = 60_000,
) -> FlareSolverrSolution:
    """GET ``url`` through FlareSolverr and return cookies + User-Agent."""
    body: dict[str, Any] = {
        "cmd": "request.get",
        "url": url,
        "maxTimeout": timeout_ms,
    }
    if session_id:
        body["session"] = session_id
    payload = _post(base_url, body, timeout_ms=timeout_ms)
    solution = payload.get("solution")
    if not isinstance(solution, dict):
        raise FlareSolverrError("FlareSolverr response missing solution")

    cookies = solution.get("cookies")
    if not isinstance(cookies, list):
        cookies = []
    user_agent = solution.get("userAgent")
    if not isinstance(user_agent, str) or not user_agent.strip():
        raise FlareSolverrError("FlareSolverr solution missing userAgent")
    status = solution.get("status")
    if not isinstance(status, int):
        status = 0
    return FlareSolverrSolution(cookies=cookies, user_agent=user_agent.strip(), status=status)


def apply_cookies(client: httpx.Client, cookies: list[dict[str, Any]]) -> None:
    """Copy FlareSolverr cookie objects onto an httpx client jar."""
    for cookie in cookies:
        name = cookie.get("name")
        value = cookie.get("value")
        if not isinstance(name, str) or not isinstance(value, str):
            continue
        domain = cookie.get("domain")
        path = cookie.get("path") or "/"
        kwargs: dict[str, Any] = {"name": name, "value": value, "path": path}
        if isinstance(domain, str) and domain:
            kwargs["domain"] = domain
        client.cookies.set(**kwargs)


def _post(base_url: str, body: dict[str, Any], *, timeout_ms: int) -> dict[str, Any]:
    endpoint = urljoin(base_url.rstrip("/") + "/", "v1")
    # Allow headroom over FlareSolverr's own maxTimeout for challenge solves.
    http_timeout = max(30.0, (timeout_ms / 1000.0) + 15.0)
    try:
        resp = httpx.post(endpoint, json=body, timeout=http_timeout)
        resp.raise_for_status()
        payload = resp.json()
    except httpx.HTTPError as exc:
        raise FlareSolverrError(f"FlareSolverr request failed: {exc}") from exc
    except ValueError as exc:
        raise FlareSolverrError("FlareSolverr returned invalid JSON") from exc

    if not isinstance(payload, dict):
        raise FlareSolverrError("FlareSolverr returned unexpected payload")
    if payload.get("status") != "ok":
        message = payload.get("message") or "unknown error"
        raise FlareSolverrError(f"FlareSolverr error: {message}")
    return payload
