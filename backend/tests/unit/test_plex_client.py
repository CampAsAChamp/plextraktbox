"""Plex client unit tests."""

from __future__ import annotations

import httpx
import respx

from plextraktbox.clients import plex_client

PLEX_IDENTITY_XML = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<MediaContainer friendlyName="Home Plex" machineIdentifier="abc123"/>'
)


@respx.mock
def test_find_connectable_server_tries_fallback_urls() -> None:
    calls: list[str] = []

    def identity_handler(request: httpx.Request) -> httpx.Response:
        base = str(request.url).split("?")[0].removesuffix("/identity")
        calls.append(base)
        if "plex.direct" in base:
            return httpx.Response(503, text="relay unreachable")
        return httpx.Response(200, text=PLEX_IDENTITY_XML)

    respx.get(url__regex=r"https?://.*/identity").mock(side_effect=identity_handler)
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


@respx.mock
def test_test_connection_reads_identity_xml() -> None:
    respx.get("http://plex.local:32400/identity").mock(
        return_value=httpx.Response(200, text=PLEX_IDENTITY_XML)
    )

    result = plex_client.test_connection("http://plex.local:32400", "plex-token")

    assert result.ok is True
    assert result.details == {"friendly_name": "Home Plex", "machine_id": "abc123"}
