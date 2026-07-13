"""Shared HTTP cache for service client fetch calls."""

from __future__ import annotations

import ssl
from functools import lru_cache

import requests_cache
from requests.adapters import HTTPAdapter

from plextraktbox.config import get_settings
from plextraktbox.ssl_compat import create_default_context_is_relaxed

# One hour — enough to dedupe repeated fetches within a run and across back-to-back jobs.
DEFAULT_CACHE_SECONDS = 3600


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


def _cached_session(cache_name: str) -> requests_cache.CachedSession:
    return requests_cache.CachedSession(
        cache_name=cache_name,
        backend="sqlite",
        expire_after=DEFAULT_CACHE_SECONDS,
        allowable_methods=("GET", "POST"),
        stale_if_error=True,
    )


@lru_cache
def get_cached_requests_session() -> requests_cache.CachedSession:
    """Return a process-wide requests session backed by SQLite in ``data_dir``."""
    settings = get_settings()
    session = _cached_session(str(settings.data_dir / "http_cache"))
    if create_default_context_is_relaxed():
        _mount_https_adapter(session, _RelaxedHTTPSAdapter())
    return session


@lru_cache
def get_plex_server_requests_session(verify_ssl: bool) -> requests_cache.CachedSession:
    """Cached requests session for Plex Media Server API calls.

    Separate from the global session so insecure TLS for ``*.plex.direct`` URLs
    does not affect Plex.tv or other HTTPS clients.
    """
    settings = get_settings()
    suffix = "plex_server" if verify_ssl else "plex_server_noverify"
    session = _cached_session(str(settings.data_dir / f"http_cache_{suffix}"))
    if verify_ssl:
        session.verify = True
        if create_default_context_is_relaxed():
            _mount_https_adapter(session, _RelaxedHTTPSAdapter())
        return session

    session.verify = False
    adapter = _PlexInsecureHTTPSAdapter()
    _mount_https_adapter(session, adapter)
    session.mount("http://", adapter)
    return session
