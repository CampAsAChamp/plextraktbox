"""Shared HTTP cache for service client fetch calls."""

from __future__ import annotations

import logging
import ssl
from functools import lru_cache
from typing import Any

import requests_cache
import urllib3
from requests.adapters import HTTPAdapter
from requests_cache.session import CacheActions

from plextraktbox.config import get_settings
from plextraktbox.ssl_compat import create_default_context_is_relaxed

logger = logging.getLogger("requests_cache.session")

# One hour — enough to dedupe repeated fetches within a run and across back-to-back jobs.
DEFAULT_CACHE_SECONDS = 3600


class _QuietCachedSession(requests_cache.CachedSession):
    """Cached session that logs stale-if-error recovery without a traceback."""

    def _handle_error(self, cached_response: Any, actions: CacheActions) -> Any:
        if actions.is_usable(cached_response, error=True):
            logger.warning(
                "Request for URL %s failed; using cached response",
                cached_response.request.url,
            )
            return cached_response
        raise


class _RelaxedHTTPSAdapter(HTTPAdapter):
    """HTTPS adapter that uses ``ssl.create_default_context`` for urllib3 pools.

    urllib3 2.x builds its own SSLContext with VERIFY_X509_STRICT on Python 3.13+,
    bypassing the global ``ssl_compat`` monkey-patch that httpx relies on.
    """

    def init_poolmanager(self, connections, maxsize, block=False, **pool_kwargs):
        pool_kwargs["ssl_context"] = ssl.create_default_context()
        return super().init_poolmanager(connections, maxsize, block=block, **pool_kwargs)


class _PlexInsecureHTTPSAdapter(HTTPAdapter):
    """HTTPS adapter that skips certificate verification for Plex ``*.plex.direct`` hosts."""

    def init_poolmanager(self, connections, maxsize, block=False, **pool_kwargs):
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        strict = getattr(ssl, "VERIFY_X509_STRICT", 0)
        partial = getattr(ssl, "VERIFY_X509_PARTIAL_CHAIN", 0)
        if strict:
            ctx.verify_flags &= ~strict
        if partial:
            ctx.verify_flags &= ~partial
        pool_kwargs["ssl_context"] = ctx
        return super().init_poolmanager(connections, maxsize, block=block, **pool_kwargs)


def _mount_https_adapter(session: requests_cache.CachedSession, adapter: HTTPAdapter) -> None:
    session.mount("https://", adapter)


def _wrap_request_verify(session: requests_cache.CachedSession, verify: bool) -> None:
    """Pin TLS verification for every outbound request on this session."""
    original_request = session.request

    def request(method: str, url: str, **kwargs: Any) -> Any:
        kwargs["verify"] = verify
        return original_request(method, url, **kwargs)

    session.request = request  # type: ignore[assignment]


def _cached_session(cache_name: str) -> _QuietCachedSession:
    return _QuietCachedSession(
        cache_name=cache_name,
        backend="sqlite",
        expire_after=DEFAULT_CACHE_SECONDS,
        allowable_methods=("GET", "POST"),
        stale_if_error=True,
    )


@lru_cache
def get_cached_requests_session() -> _QuietCachedSession:
    """Return a process-wide requests session backed by SQLite in ``data_dir``."""
    settings = get_settings()
    session = _cached_session(str(settings.data_dir / "http_cache"))
    if create_default_context_is_relaxed():
        _mount_https_adapter(session, _RelaxedHTTPSAdapter())
    return session


@lru_cache
def get_plex_server_requests_session(verify_ssl: bool) -> _QuietCachedSession:
    """Cached requests session for Plex Media Server API calls.

    Separate from the global session so insecure TLS for ``*.plex.direct`` URLs
    does not affect Plex.tv or other HTTPS clients.
    """
    settings = get_settings()
    suffix = "plex_server" if verify_ssl else "plex_server_noverify"
    session = _cached_session(str(settings.data_dir / f"http_cache_{suffix}"))
    if verify_ssl:
        session.verify = True
        _wrap_request_verify(session, True)
        if create_default_context_is_relaxed():
            _mount_https_adapter(session, _RelaxedHTTPSAdapter())
        return session

    # *.plex.direct uses a Plex CA that fails Python 3.13+ strict checks; we
    # intentionally skip verify. Suppress urllib3's per-request noise.
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    session.verify = False
    adapter = _PlexInsecureHTTPSAdapter()
    _mount_https_adapter(session, adapter)
    session.mount("http://", adapter)
    _wrap_request_verify(session, False)
    return session
