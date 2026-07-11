"""Connections API tests."""

from __future__ import annotations

import httpx
import respx
from fastapi.testclient import TestClient

HEADERS = {"X-Requested-With": "XMLHttpRequest"}


def _create_user_and_login(client: TestClient) -> None:
    client.post(
        "/api/setup/user",
        json={
            "username": "nick",
            "email": "nick@example.com",
            "password": "supersecret",
        },
        headers=HEADERS,
    )
    client.post(
        "/api/auth/login",
        json={"username": "nick", "password": "supersecret"},
        headers=HEADERS,
    )


def test_connections_status_requires_auth(client: TestClient) -> None:
    _create_user_and_login(client)
    client.post("/api/auth/logout", headers=HEADERS)
    resp = client.get("/api/connections/status")
    assert resp.status_code == 401


def test_connections_status_initially_needs_setup(client: TestClient) -> None:
    _create_user_and_login(client)
    resp = client.get("/api/connections/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["needs_connections"] is True
    assert len(data["connections"]) == 4
    assert all(item["status"] == "unconfigured" for item in data["connections"])


@respx.mock
def test_save_tmdb_connection(client: TestClient) -> None:
    _create_user_and_login(client)
    respx.get("https://api.themoviedb.org/3/configuration").mock(
        return_value=httpx.Response(200, json={"images": {}})
    )

    resp = client.post(
        "/api/connections/tmdb",
        json={"api_key": "test-key"},
        headers=HEADERS,
    )
    assert resp.status_code == 200
    assert resp.json()["service"] == "tmdb"
    assert resp.json()["status"] == "ok"

    status = client.get("/api/connections/status").json()
    tmdb = next(c for c in status["connections"] if c["service"] == "tmdb")
    assert tmdb["status"] == "ok"
    assert "api_key" not in tmdb["config"]


@respx.mock
def test_plex_pin_flow(client: TestClient, monkeypatch) -> None:
    _create_user_and_login(client)

    class FakeServer:
        friendlyName = "Home Plex"
        machineIdentifier = "abc123"

    monkeypatch.setattr(
        "plextraktbox.clients.plex_client.PlexServer",
        lambda url, token, timeout=10: FakeServer(),
    )

    respx.post("https://plex.tv/api/v2/pins").mock(
        return_value=httpx.Response(
            200,
            json={"id": 42, "code": "ABCD"},
        )
    )
    respx.get("https://plex.tv/api/v2/pins/42").mock(
        return_value=httpx.Response(
            200,
            json={"id": 42, "code": "ABCD", "authToken": "plex-account-token"},
        )
    )
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
                    "accessToken": "plex-server-token",
                    "connections": [
                        {
                            "uri": "http://plex.local:32400",
                            "local": True,
                            "relay": False,
                            "protocol": "http",
                        }
                    ],
                }
            ],
        )
    )

    start = client.post("/api/connections/plex/pin/start", headers=HEADERS)
    assert start.status_code == 200
    start_body = start.json()
    assert start_body["pin_id"] == 42
    assert "app.plex.tv/auth/#!?" in start_body["auth_url"]

    poll = client.post(
        "/api/connections/plex/pin/poll",
        json={"pin_id": start_body["pin_id"], "pin_code": start_body["pin_code"]},
        headers=HEADERS,
    )
    assert poll.status_code == 200
    poll_body = poll.json()
    assert poll_body["status"] == "ok"
    assert poll_body["connection"]["service"] == "plex"
    assert poll_body["connection"]["status"] == "ok"
    assert poll_body["connection"]["config"]["url"] == "http://plex.local:32400"


@respx.mock
def test_plex_pin_poll_pending(client: TestClient) -> None:
    _create_user_and_login(client)
    respx.post("https://plex.tv/api/v2/pins").mock(
        return_value=httpx.Response(200, json={"id": 7, "code": "WXYZ"})
    )
    respx.get("https://plex.tv/api/v2/pins/7").mock(
        return_value=httpx.Response(200, json={"id": 7, "code": "WXYZ", "authToken": None})
    )

    start = client.post("/api/connections/plex/pin/start", headers=HEADERS).json()
    poll = client.post(
        "/api/connections/plex/pin/poll",
        json={"pin_id": start["pin_id"], "pin_code": start["pin_code"]},
        headers=HEADERS,
    )
    assert poll.status_code == 200
    assert poll.json()["status"] == "pending"


@respx.mock
def test_save_plex_connection(client: TestClient, monkeypatch) -> None:
    _create_user_and_login(client)

    class FakeServer:
        friendlyName = "Home Plex"
        machineIdentifier = "abc123"

    monkeypatch.setattr(
        "plextraktbox.clients.plex_client.PlexServer",
        lambda url, token, timeout=10: FakeServer(),
    )

    resp = client.post(
        "/api/connections/plex",
        json={"url": "http://plex.local:32400", "token": "plex-token"},
        headers=HEADERS,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["service"] == "plex"
    assert body["status"] == "ok"
    assert body["config"]["url"] == "http://plex.local:32400"


@respx.mock
def test_save_letterboxd_connection(client: TestClient) -> None:
    _create_user_and_login(client)
    respx.get("https://letterboxd.com/sign-in/").mock(
        return_value=httpx.Response(
            200,
            text="<html></html>",
            headers={"set-cookie": "com.xk72.webparts.csrf=test-csrf; Path=/; HttpOnly"},
        )
    )
    respx.post("https://letterboxd.com/user/login.do").mock(
        return_value=httpx.Response(
            302,
            headers={
                "location": "/nick/",
                "set-cookie": "letterboxd.signed.in.as=nick; Path=/",
            },
        )
    )

    resp = client.post(
        "/api/connections/letterboxd",
        json={"username": "nick", "password": "lb-pass"},
        headers=HEADERS,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["service"] == "letterboxd"
    assert body["status"] == "ok"
    assert body["config"]["username"] == "nick"


@respx.mock
def test_save_letterboxd_keeps_password_when_omitted(client: TestClient) -> None:
    _create_user_and_login(client)
    respx.get("https://letterboxd.com/sign-in/").mock(
        return_value=httpx.Response(
            200,
            text="<html></html>",
            headers={"set-cookie": "com.xk72.webparts.csrf=test-csrf; Path=/; HttpOnly"},
        )
    )
    respx.post("https://letterboxd.com/user/login.do").mock(
        return_value=httpx.Response(
            302,
            headers={
                "location": "/nick/",
                "set-cookie": "letterboxd.signed.in.as=nick; Path=/",
            },
        )
    )

    initial = client.post(
        "/api/connections/letterboxd",
        json={"username": "nick", "password": "lb-pass"},
        headers=HEADERS,
    )
    assert initial.status_code == 200

    updated = client.post(
        "/api/connections/letterboxd",
        json={"username": "nick2"},
        headers=HEADERS,
    )
    assert updated.status_code == 200
    assert updated.json()["config"]["username"] == "nick2"

    test_resp = client.post(
        "/api/connections/letterboxd/test",
        json={"username": "nick2"},
        headers=HEADERS,
    )
    assert test_resp.status_code == 200
    assert test_resp.json()["ok"] is True


def test_trakt_device_start_requires_credentials(client: TestClient, monkeypatch) -> None:
    _create_user_and_login(client)
    monkeypatch.delenv("TRAKT_CLIENT_ID", raising=False)
    monkeypatch.delenv("TRAKT_CLIENT_SECRET", raising=False)

    from plextraktbox import config

    config.get_settings.cache_clear()

    resp = client.post("/api/connections/trakt/device/start", headers=HEADERS)
    assert resp.status_code == 503
    assert "not configured" in resp.json()["detail"].lower()


@respx.mock
def test_trakt_device_flow(client: TestClient) -> None:
    _create_user_and_login(client)
    respx.post("https://api.trakt.tv/oauth/device/code").mock(
        return_value=httpx.Response(
            200,
            json={
                "user_code": "ABCD1234",
                "device_code": "device-code-xyz",
                "verification_url": "https://trakt.tv/activate",
                "expires_in": 600,
                "interval": 5,
            },
        )
    )
    respx.post("https://api.trakt.tv/oauth/device/token").mock(
        return_value=httpx.Response(
            200,
            json={
                "access_token": "access",
                "refresh_token": "refresh",
                "expires_in": 7200,
            },
        )
    )
    respx.get("https://api.trakt.tv/users/settings").mock(
        return_value=httpx.Response(200, json={"user": {"username": "nick"}})
    )

    start = client.post(
        "/api/connections/trakt/device/start",
        headers=HEADERS,
    )
    assert start.status_code == 200
    start_body = start.json()
    assert start_body["user_code"] == "ABCD1234"

    poll = client.post(
        "/api/connections/trakt/device/poll",
        json={
            "device_code": start_body["device_code"],
        },
        headers=HEADERS,
    )
    assert poll.status_code == 200
    poll_body = poll.json()
    assert poll_body["status"] == "ok"
    assert poll_body["connection"]["service"] == "trakt"
    assert poll_body["connection"]["status"] == "ok"
    assert poll_body["connection"]["config"] == {}


@respx.mock
def test_all_connections_configured(client: TestClient, monkeypatch) -> None:
    _create_user_and_login(client)

    class FakeServer:
        friendlyName = "Home Plex"
        machineIdentifier = "abc123"

    monkeypatch.setattr(
        "plextraktbox.clients.plex_client.PlexServer",
        lambda url, token, timeout=10: FakeServer(),
    )
    respx.post("https://plex.tv/api/v2/pins").mock(
        return_value=httpx.Response(200, json={"id": 42, "code": "ABCD"})
    )
    respx.get("https://plex.tv/api/v2/pins/42").mock(
        return_value=httpx.Response(
            200,
            json={"id": 42, "code": "ABCD", "authToken": "plex-account-token"},
        )
    )
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
                    "accessToken": "plex-server-token",
                    "connections": [
                        {
                            "uri": "http://plex.local:32400",
                            "local": True,
                            "relay": False,
                            "protocol": "http",
                        }
                    ],
                }
            ],
        )
    )
    respx.get("https://api.themoviedb.org/3/configuration").mock(
        return_value=httpx.Response(200, json={"images": {}})
    )
    respx.get("https://letterboxd.com/sign-in/").mock(
        return_value=httpx.Response(
            200,
            text="<html></html>",
            headers={"set-cookie": "com.xk72.webparts.csrf=test-csrf; Path=/; HttpOnly"},
        )
    )
    respx.post("https://letterboxd.com/user/login.do").mock(
        return_value=httpx.Response(
            302,
            headers={
                "location": "/nick/",
                "set-cookie": "letterboxd.signed.in.as=nick; Path=/",
            },
        )
    )
    respx.post("https://api.trakt.tv/oauth/device/code").mock(
        return_value=httpx.Response(
            200,
            json={
                "user_code": "ABCD1234",
                "device_code": "device-code-xyz",
                "verification_url": "https://trakt.tv/activate",
                "expires_in": 600,
                "interval": 5,
            },
        )
    )
    respx.post("https://api.trakt.tv/oauth/device/token").mock(
        return_value=httpx.Response(
            200,
            json={
                "access_token": "access",
                "refresh_token": "refresh",
                "expires_in": 7200,
            },
        )
    )
    respx.get("https://api.trakt.tv/users/settings").mock(
        return_value=httpx.Response(200, json={"user": {"username": "nick"}})
    )

    plex_start = client.post("/api/connections/plex/pin/start", headers=HEADERS).json()
    client.post(
        "/api/connections/plex/pin/poll",
        json={"pin_id": plex_start["pin_id"], "pin_code": plex_start["pin_code"]},
        headers=HEADERS,
    )
    client.post(
        "/api/connections/letterboxd",
        json={"username": "nick", "password": "lb-pass"},
        headers=HEADERS,
    )
    client.post(
        "/api/connections/tmdb",
        json={"api_key": "test-key"},
        headers=HEADERS,
    )
    start = client.post(
        "/api/connections/trakt/device/start",
        headers=HEADERS,
    ).json()
    client.post(
        "/api/connections/trakt/device/poll",
        json={
            "device_code": start["device_code"],
        },
        headers=HEADERS,
    )

    status = client.get("/api/connections/status").json()
    assert status["needs_connections"] is False
    assert all(item["status"] == "ok" for item in status["connections"])


@respx.mock
def test_clear_connection(client: TestClient) -> None:
    _create_user_and_login(client)
    respx.get("https://api.themoviedb.org/3/configuration").mock(
        return_value=httpx.Response(200, json={"images": {}})
    )
    client.post(
        "/api/connections/tmdb",
        json={"api_key": "test-key"},
        headers=HEADERS,
    )

    resp = client.delete("/api/connections/tmdb", headers=HEADERS)
    assert resp.status_code == 204

    status = client.get("/api/connections/status").json()
    tmdb = next(c for c in status["connections"] if c["service"] == "tmdb")
    assert tmdb["status"] == "unconfigured"
    assert status["needs_connections"] is True


@respx.mock
def test_clear_all_connections(client: TestClient) -> None:
    _create_user_and_login(client)
    respx.get("https://api.themoviedb.org/3/configuration").mock(
        return_value=httpx.Response(200, json={"images": {}})
    )
    client.post(
        "/api/connections/tmdb",
        json={"api_key": "test-key"},
        headers=HEADERS,
    )

    status = client.get("/api/connections/status").json()
    assert any(item["status"] == "ok" for item in status["connections"])

    resp = client.delete("/api/connections", headers=HEADERS)
    assert resp.status_code == 204

    status = client.get("/api/connections/status").json()
    assert status["needs_connections"] is True
    assert all(item["status"] == "unconfigured" for item in status["connections"])
