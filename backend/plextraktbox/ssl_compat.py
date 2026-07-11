"""Python 3.13+ SSL compatibility for corporate TLS-inspecting proxies.

Zscaler and similar proxies ship root CAs whose Basic Constraints extension is
not marked critical. Python 3.13 enables VERIFY_X509_STRICT by default, which
rejects those chains even when the CA is explicitly trusted via SSL_CERT_FILE.
"""

from __future__ import annotations

import os
import ssl
import sys
from typing import Any

from plextraktbox.logging_setup import get_logger

log = get_logger(__name__)

_STRICT = getattr(ssl, "VERIFY_X509_STRICT", 0)
_PARTIAL = getattr(ssl, "VERIFY_X509_PARTIAL_CHAIN", 0)
_ORIGINAL_CREATE_DEFAULT_CONTEXT = ssl.create_default_context
_PATCHED = False


def _custom_ca_bundle_configured() -> bool:
    """True when the process trusts a non-default CA bundle (e.g. Zscaler in Docker)."""
    for env_var in ("SSL_CERT_FILE", "REQUESTS_CA_BUNDLE", "CURL_CA_BUNDLE"):
        if os.environ.get(env_var):
            return True
    return False


def _relaxed_create_default_context(*args: Any, **kwargs: Any) -> ssl.SSLContext:
    ctx = _ORIGINAL_CREATE_DEFAULT_CONTEXT(*args, **kwargs)
    if _STRICT:
        ctx.verify_flags &= ~_STRICT
    if _PARTIAL:
        ctx.verify_flags &= ~_PARTIAL
    return ctx


def configure_ssl_compat() -> None:
    """Relax X.509 strict checks when a custom CA bundle is configured."""
    global _PATCHED
    if _PATCHED:
        return
    if sys.version_info < (3, 13):
        return
    if _STRICT == 0 and _PARTIAL == 0:
        return
    if not _custom_ca_bundle_configured():
        return

    ssl.create_default_context = _relaxed_create_default_context  # type: ignore[assignment]
    _PATCHED = True
    log.info(
        "ssl_compat.relaxed_strict_checks",
        reason="Python 3.13+ VERIFY_X509_STRICT rejects some corporate root CAs",
    )


def create_default_context_is_relaxed() -> bool:
    """Return whether the ssl.create_default_context monkey-patch is active."""
    return _PATCHED and ssl.create_default_context is _relaxed_create_default_context


__all__ = ["configure_ssl_compat", "create_default_context_is_relaxed"]
