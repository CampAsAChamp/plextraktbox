"""Plex client unit tests."""

from __future__ import annotations

import httpx
import respx
from plexapi.exceptions import PlexApiException

from plextraktbox.clients import plex_client


@respx.mock
def test_find_connectable_server_tries_fallback_urls(monkeypatch) -> None:
    calls: list[str] = []

    class FakeServer:
        friendlyName = "Home Plex"
        machineIdentifier = "abc123"

    def fake_plex_server(url: str, token: str, timeout: int = 10) -> FakeServer:
        calls.append(url)
        if "plex.direct" in url:
            raise PlexApiException("relay unreachable")
        return FakeServer()

    monkeypatch.setattr("plextraktbox.clients.plex_client.PlexServer", fake_plex_server)
    respx.get("https://plex.tv/api/v2/resources").mock(
        return_value=httpx.Response(
            200,
            json=[
                {
                    "name": "Home Plex",
                    "product": "Plex Media Server",
                    "provides": "server",
                    "owned": True,
                    "clientIdentifier": "abc123",
                    "accessToken": "server-token",
                    "connections": [
                        {
                            "uri": "http://192.168.1.10:32400",
                            "local": True,
                            "relay": False,
                            "protocol": "http",
                        },
                        {
                            "uri": "https://10-0-0-25.abc.plex.direct:32400",
                            "local": False,
                            "relay": True,
                            "protocol": "https",
                        },
                    ],
                }
            ],
        )
    )

    server, result = plex_client.find_connectable_server("account-token", "client-id")

    assert server is not None
    assert result is not None
    assert result.ok is True
    assert server.url == "http://192.168.1.10:32400"
    assert calls[0].endswith(".plex.direct:32400")
    assert "http://192.168.1.10:32400" in calls
    assert calls.index("http://192.168.1.10:32400") > 0
