"""Tests for shared HTTP cache sessions."""

from __future__ import annotations

import os
import ssl
from unittest.mock import patch

import pytest

from plextraktbox import ssl_compat
from plextraktbox.clients import http_cache


@pytest.fixture(autouse=True)
def _reset_ssl_and_session_caches() -> None:
    """Isolate tests from global SSL patch and lru_cached sessions."""
    ssl.create_default_context = ssl_compat._ORIGINAL_CREATE_DEFAULT_CONTEXT
    ssl_compat._PATCHED = False
    http_cache.get_cached_requests_session.cache_clear()
    http_cache.get_plex_server_requests_session.cache_clear()
    yield
    ssl.create_default_context = ssl_compat._ORIGINAL_CREATE_DEFAULT_CONTEXT
    ssl_compat._PATCHED = False
    http_cache.get_cached_requests_session.cache_clear()
    http_cache.get_plex_server_requests_session.cache_clear()


def _adapter_ssl_context(session, url: str = "https://example.com") -> ssl.SSLContext:
    adapter = session.get_adapter(url)
    return adapter.poolmanager.connection_pool_kw["ssl_context"]


def test_cached_session_uses_relaxed_adapter_when_custom_ca_set() -> None:
    if not hasattr(ssl, "VERIFY_X509_STRICT"):
        pytest.skip("VERIFY_X509_STRICT not available")

    with patch.dict(os.environ, {"SSL_CERT_FILE": "/etc/ssl/certs/zscaler-root-ca.pem"}, clear=True):
        ssl_compat.configure_ssl_compat()
        session = http_cache.get_cached_requests_session()

    ctx = _adapter_ssl_context(session)
    assert not (ctx.verify_flags & ssl.VERIFY_X509_STRICT)


def test_plex_server_verify_session_uses_relaxed_adapter_when_custom_ca_set() -> None:
    if not hasattr(ssl, "VERIFY_X509_STRICT"):
        pytest.skip("VERIFY_X509_STRICT not available")

    with patch.dict(os.environ, {"SSL_CERT_FILE": "/etc/ssl/certs/zscaler-root-ca.pem"}, clear=True):
        ssl_compat.configure_ssl_compat()
        session = http_cache.get_plex_server_requests_session(True)

    ctx = _adapter_ssl_context(session)
    assert not (ctx.verify_flags & ssl.VERIFY_X509_STRICT)


def test_cached_session_keeps_default_adapter_without_custom_ca() -> None:
    with patch.dict(os.environ, {}, clear=True):
        ssl_compat.configure_ssl_compat()
        session = http_cache.get_cached_requests_session()

    adapter = session.get_adapter("https://example.com")
    assert type(adapter).__name__ == "HTTPAdapter"
