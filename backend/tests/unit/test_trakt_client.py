"""Trakt client tests."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import httpx
import respx

from plextraktbox.clients import trakt_client


@respx.mock
def test_test_connection_accepts_naive_token_expires_at() -> None:
    respx.post("https://api.trakt.tv/oauth/token").mock(
        return_value=httpx.Response(
            200,
            json={
                "access_token": "new-access",
                "refresh_token": "new-refresh",
                "expires_in": 7200,
            },
        )
    )
    respx.get("https://api.trakt.tv/users/settings").mock(
        return_value=httpx.Response(200, json={"user": {"username": "nick"}})
    )

    naive_expired = datetime.now(UTC).replace(tzinfo=None) - timedelta(hours=1)

    result, refreshed = trakt_client.test_connection(
        "client-id",
        "client-secret",
        "old-access",
        "old-refresh",
        token_expires_at=naive_expired,
    )

    assert result.ok is True
    assert result.message == "Connected to Trakt"
    assert refreshed is not None
    assert refreshed.access_token == "new-access"
