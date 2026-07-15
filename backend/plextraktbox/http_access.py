"""Inbound HTTP access logging with service context derived from API paths."""

from __future__ import annotations

import re
from collections.abc import Awaitable, Callable
from typing import Literal

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from plextraktbox.logging_setup import get_logger
from plextraktbox.models.connection import Service

log = get_logger(__name__)

_CONNECTIONS_PREFIX = "/api/connections/"
_SKIP_LOG_PATHS = frozenset(
    {
        "/api/health",
        "/api/notifications/inapp/unread-count",
    }
)
# Run detail is polled every ~2s while a sync is running — keep out of INFO.
_DEBUG_LOG_PATH_RE = re.compile(r"^/api/runs/\d+$")

AccessLogLevel = Literal["info", "debug"]


def should_log_access(path: str) -> bool:
    """Return False for high-frequency polling routes that add log noise."""
    return path not in _SKIP_LOG_PATHS


def access_log_level(method: str, path: str) -> AccessLogLevel | None:
    """Return the level for an access log line, or None to skip."""
    if not should_log_access(path):
        return None
    if method == "GET" and _DEBUG_LOG_PATH_RE.match(path):
        return "debug"
    return "info"


def service_from_path(path: str) -> str | None:
    """Return an uppercase service label when the path targets a connection route."""
    if not path.startswith(_CONNECTIONS_PREFIX):
        return None
    segment = path[len(_CONNECTIONS_PREFIX) :].split("/", 1)[0]
    try:
        return Service(segment).name
    except ValueError:
        return None


def format_access_log_line(
    method: str,
    path: str,
    *,
    service: str | None = None,
    status_code: int | None = None,
) -> str:
    service_label = f"{service} " if service else ""
    line = f"{method} {service_label}{path}"
    if status_code is not None:
        return f"{line} {status_code}"
    return line


class AccessLogMiddleware(BaseHTTPMiddleware):
    """Log API requests in a compact access-log style with optional service tags."""

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        response = await call_next(request)
        path = request.url.path
        level = access_log_level(request.method, path)
        if level is not None:
            service = service_from_path(path)
            getattr(log, level)(
                format_access_log_line(
                    request.method,
                    path,
                    service=service,
                    status_code=response.status_code,
                ),
                method=request.method,
                path=path,
                service=service,
                status_code=response.status_code,
            )
        return response
