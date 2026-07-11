"""Plex auth URL unit tests."""

from __future__ import annotations

from plextraktbox.clients.plex_client import _build_auth_url


def test_build_auth_url_uses_plex_oauth_format() -> None:
    url = _build_auth_url("client-id-123", "pin-code-xyz")
    assert url.startswith("https://app.plex.tv/auth/#!?")
    assert "clientID=client-id-123" in url
    assert "code=pin-code-xyz" in url
    assert "context%5Bdevice%5D%5Bproduct%5D=plextraktbox" in url
