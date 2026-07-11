"""Jobs API tests."""

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


@respx.mock
def _configure_connections(client: TestClient, monkeypatch) -> None:
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
    client.post("/api/connections/tmdb", json={"api_key": "test-key"}, headers=HEADERS)
    trakt_start = client.post("/api/connections/trakt/device/start", headers=HEADERS).json()
    client.post(
        "/api/connections/trakt/device/poll",
        json={"device_code": trakt_start["device_code"]},
        headers=HEADERS,
    )


def test_jobs_require_auth(client: TestClient) -> None:
    _create_user_and_login(client)
    client.post("/api/auth/logout", headers=HEADERS)
    resp = client.get("/api/jobs")
    assert resp.status_code == 401


@respx.mock
def test_create_and_run_plex_trakt_job(client: TestClient, monkeypatch) -> None:
    _create_user_and_login(client)
    _configure_connections(client, monkeypatch)

    create = client.post(
        "/api/jobs",
        json={
            "name": "Plex ↔ Trakt",
            "source_pair": "plex_trakt",
            "data_types": ["watchlist", "watched"],
            "dry_run": True,
        },
        headers=HEADERS,
    )
    assert create.status_code == 200
    job = create.json()
    assert job["name"] == "Plex ↔ Trakt"
    assert job["source_pair"] == "plex_trakt"

    run = client.post(f"/api/jobs/{job['id']}/run", headers=HEADERS)
    assert run.status_code == 200
    body = run.json()
    assert body["status"] == "success"
    assert body["dry_run"] is True
    assert body["summary"]["planned"] >= 0


def test_create_job_validates_data_types(client: TestClient) -> None:
    _create_user_and_login(client)
    resp = client.post(
        "/api/jobs",
        json={
            "name": "Bad job",
            "source_pair": "letterboxd_plex",
            "data_types": ["watchlist"],
        },
        headers=HEADERS,
    )
    assert resp.status_code == 400
    assert "watchlist" in resp.json()["detail"]
