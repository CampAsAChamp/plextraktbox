"""Session middleware with adaptive Secure cookies.

Starlette's ``SessionMiddleware`` bakes ``Secure`` in at construction time. That
breaks TrueNAS installs that use both LAN HTTP and Cloudflare Tunnel HTTPS.
This wrapper sets ``Secure`` per response when mode is ``auto``.
"""

from __future__ import annotations

from typing import Literal

from starlette.datastructures import MutableHeaders, Secret
from starlette.middleware.sessions import SessionMiddleware
from starlette.types import ASGIApp, Message, Receive, Scope, Send

HttpsOnlyMode = Literal["auto", "always", "never"]


def client_is_https(scope: Scope) -> bool:
    """Return True when the browser-facing connection is HTTPS.

    Prefers the ASGI scheme, then the first ``X-Forwarded-Proto`` value (set by
    Cloudflare Tunnel and most reverse proxies).
    """
    if scope.get("scheme") == "https":
        return True
    for name, value in scope.get("headers", []):
        if name == b"x-forwarded-proto":
            first = value.decode("latin-1").split(",", 1)[0].strip().lower()
            return first == "https"
    return False


def should_set_secure_cookie(mode: HttpsOnlyMode, scope: Scope) -> bool:
    if mode == "always":
        return True
    if mode == "never":
        return False
    return client_is_https(scope)


class AdaptiveSessionMiddleware:
    """Session cookies with HttpOnly + SameSite=Lax and adaptive Secure."""

    def __init__(
        self,
        app: ASGIApp,
        secret_key: str | Secret,
        session_cookie: str = "session",
        max_age: int | None = 14 * 24 * 60 * 60,
        path: str = "/",
        same_site: Literal["lax", "strict", "none"] = "lax",
        https_only: HttpsOnlyMode = "auto",
        domain: str | None = None,
    ) -> None:
        self.https_only = https_only
        self.session_cookie = session_cookie
        # Always construct without Secure; we add it per-response when needed.
        self.app = SessionMiddleware(
            app,
            secret_key=secret_key,
            session_cookie=session_cookie,
            max_age=max_age,
            path=path,
            same_site=same_site,
            https_only=False,
            domain=domain,
        )

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in ("http", "websocket"):  # pragma: no cover
            await self.app(scope, receive, send)
            return

        secure = should_set_secure_cookie(self.https_only, scope)
        cookie_prefix = f"{self.session_cookie}=".encode("latin-1")

        async def send_wrapper(message: Message) -> None:
            if secure and message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                # MutableHeaders may list the same name more than once; rebuild
                # set-cookie values so our session cookie gains Secure.
                cookies = headers.getlist("set-cookie")
                if cookies:
                    del headers["set-cookie"]
                    for cookie in cookies:
                        is_session = cookie.encode("latin-1").startswith(cookie_prefix)
                        if is_session and "; secure" not in cookie.lower():
                            cookie = f"{cookie}; Secure"
                        headers.append("set-cookie", cookie)
            await send(message)

        await self.app(scope, receive, send_wrapper)
