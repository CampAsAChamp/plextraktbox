"""Tests for corporate-proxy SSL compatibility."""

from __future__ import annotations

import os
import ssl
from unittest.mock import patch

import pytest

from plextraktbox import ssl_compat


@pytest.fixture(autouse=True)
def _reset_ssl_patch() -> None:
    """Isolate tests from the global ssl.create_default_context monkey-patch."""
    ssl.create_default_context = ssl_compat._ORIGINAL_CREATE_DEFAULT_CONTEXT
    ssl_compat._PATCHED = False
    yield
    ssl.create_default_context = ssl_compat._ORIGINAL_CREATE_DEFAULT_CONTEXT
    ssl_compat._PATCHED = False


def test_configure_ssl_compat_skips_without_custom_ca() -> None:
    with patch.dict(os.environ, {}, clear=True):
        ssl_compat.configure_ssl_compat()
    assert not ssl_compat.create_default_context_is_relaxed()


def test_configure_ssl_compat_relaxes_when_custom_ca_set() -> None:
    if not hasattr(ssl, "VERIFY_X509_STRICT"):
        pytest.skip("VERIFY_X509_STRICT not available")

    with patch.dict(os.environ, {"SSL_CERT_FILE": "/etc/ssl/certs/zscaler-root-ca.pem"}, clear=True):
        ssl_compat.configure_ssl_compat()

    assert ssl_compat.create_default_context_is_relaxed()
    ctx = ssl.create_default_context()
    assert not (ctx.verify_flags & ssl.VERIFY_X509_STRICT)
