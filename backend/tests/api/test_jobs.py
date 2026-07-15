"""Jobs API tests."""

from __future__ import annotations

import httpx
import pytest
import respx
from fastapi.testclient import TestClient

HEADERS = {"X-Requested-With": "XMLHttpRequest"}


def _mock_live_fetch(monkeypatch: pytest.MonkeyPatch) -> None:
    """Avoid live Plex/Trakt/Letterboxd HTTP during scheduler-backed job runs."""
    from plextraktbox.sync.sources.letterboxd_source import LetterboxdSource

    async def empty_fetch(*args: object, **kwargs: object) -> list:
        return []

    monkeypatch.setattr(
        "plextraktbox.services.connections.ensure_trakt_access_token",
        lambda session, connection: "access",
    )
    monkeypatch.setattr("plextraktbox.clients.plex_client.fetch_watchlist", lambda token: [])
    monkeypatch.setattr(
        "plextraktbox.clients.plex_client.fetch_watched",
        lambda url, token, library_ids=None: [],
    )
    monkeypatch.setattr(
        "plextraktbox.clients.plex_client.fetch_ratings_movies",
        lambda url, token, library_ids=None: [],
    )
    monkeypatch.setattr(
        "plextraktbox.clients.trakt_client.fetch_watchlist",
        lambda client_id, access_token: [],
    )
    monkeypatch.setattr(
        "plextraktbox.clients.trakt_client.fetch_watched",
        lambda client_id, access_token: [],
    )
    monkeypatch.setattr(
        "plextraktbox.clients.letterboxd_client.fetch_watchlist_movies",
        lambda *args, **kwargs: [],
    )
    monkeypatch.setattr(LetterboxdSource, "fetch_watchlist", empty_fetch)
    monkeypatch.setattr(LetterboxdSource, "fetch_ratings", empty_fetch)
    monkeypatch.setattr(LetterboxdSource, "fetch_watched", empty_fetch)


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
def _configure_connections(client: TestClient) -> None:
    respx.get("http://plex.local:32400/identity").mock(
        return_value=httpx.Response(
            200,
            text=(
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<MediaContainer friendlyName="Home Plex" machineIdentifier="abc123"/>'
            ),
        )
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
    respx.get("https://letterboxd.com/").mock(
        return_value=httpx.Response(
            200,
            headers={"set-cookie": "com.xk72.webparts.csrf=test-csrf; Path=/"},
        )
    )
    respx.post("https://letterboxd.com/user/login.do").mock(
        return_value=httpx.Response(
            200,
            json={"result": "success"},
            headers={"content-type": "application/json"},
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
def test_create_and_run_plex_trakt_job(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    _create_user_and_login(client)
    _configure_connections(client)
    _mock_live_fetch(monkeypatch)

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


def test_create_job_validates_cron(client: TestClient) -> None:
    _create_user_and_login(client)
    resp = client.post(
        "/api/jobs",
        json={
            "name": "Bad cron",
            "source_pair": "plex_trakt",
            "data_types": ["watchlist"],
            "cron": "not-a-cron",
        },
        headers=HEADERS,
    )
    assert resp.status_code == 422
    assert "cron" in resp.json()["detail"][0]["loc"]


def test_update_job_validates_cron(client: TestClient) -> None:
    _create_user_and_login(client)

    create = client.post(
        "/api/jobs",
        json={
            "name": "Cron job",
            "source_pair": "plex_trakt",
            "data_types": ["watchlist"],
            "cron": "0 3 * * *",
        },
        headers=HEADERS,
    )
    assert create.status_code == 200
    job_id = create.json()["id"]

    update = client.put(
        f"/api/jobs/{job_id}",
        json={
            "name": "Cron job",
            "source_pair": "plex_trakt",
            "data_types": ["watchlist"],
            "cron": "every day",
        },
        headers=HEADERS,
    )
    assert update.status_code == 422
    assert "cron" in update.json()["detail"][0]["loc"]


def test_job_crud(client: TestClient) -> None:
    _create_user_and_login(client)

    create = client.post(
        "/api/jobs",
        json={
            "name": "Original",
            "source_pair": "letterboxd_plex",
            "data_types": ["ratings"],
            "enabled": True,
            "cron": "0 4 * * *",
            "dry_run": False,
        },
        headers=HEADERS,
    )
    assert create.status_code == 200
    created = create.json()
    job_id = created["id"]
    assert created["next_run_at"] is not None

    get_resp = client.get(f"/api/jobs/{job_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["name"] == "Original"
    assert get_resp.json()["next_run_at"] is not None

    update = client.put(
        f"/api/jobs/{job_id}",
        json={
            "name": "Updated",
            "source_pair": "letterboxd_plex",
            "data_types": ["ratings"],
            "enabled": False,
            "cron": "0 5 * * *",
            "dry_run": True,
        },
        headers=HEADERS,
    )
    assert update.status_code == 200
    assert update.json()["name"] == "Updated"
    assert update.json()["enabled"] is False
    assert update.json()["dry_run"] is True
    assert update.json()["next_run_at"] is None

    delete = client.delete(f"/api/jobs/{job_id}", headers=HEADERS)
    assert delete.status_code == 204

    missing = client.get(f"/api/jobs/{job_id}")
    assert missing.status_code == 404


def test_clone_job(client: TestClient) -> None:
    _create_user_and_login(client)

    create = client.post(
        "/api/jobs",
        json={
            "name": "Original",
            "source_pair": "letterboxd_plex",
            "data_types": ["ratings"],
            "enabled": True,
            "cron": "0 4 * * *",
            "dry_run": True,
            "require_dry_run_first": False,
        },
        headers=HEADERS,
    )
    assert create.status_code == 200
    job_id = create.json()["id"]

    clone = client.post(f"/api/jobs/{job_id}/clone", headers=HEADERS)
    assert clone.status_code == 200
    body = clone.json()
    assert body["id"] != job_id
    assert body["name"] == "Original (copy)"
    assert body["enabled"] is False
    assert body["source_pair"] == "letterboxd_plex"
    assert body["data_types"] == ["ratings"]
    assert body["cron"] == "0 4 * * *"
    assert body["dry_run"] is True
    assert body["last_run"] is None
    assert body["next_run_at"] is None

    again = client.post(f"/api/jobs/{job_id}/clone", headers=HEADERS)
    assert again.status_code == 200
    assert again.json()["name"] == "Original (copy 2)"

    missing = client.post("/api/jobs/999/clone", headers=HEADERS)
    assert missing.status_code == 404


def test_job_list_includes_last_run(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    _create_user_and_login(client)
    _configure_connections(client)
    _mock_live_fetch(monkeypatch)

    create = client.post(
        "/api/jobs",
        json={
            "name": "Watchlist sync",
            "source_pair": "plex_trakt",
            "data_types": ["watchlist"],
            "enabled": True,
            "cron": "0 3 * * *",
            "dry_run": True,
            "require_dry_run_first": False,
        },
        headers=HEADERS,
    )
    assert create.status_code == 200
    job_id = create.json()["id"]
    assert create.json()["last_run"] is None

    listed = client.get("/api/jobs")
    assert listed.status_code == 200
    assert listed.json()[0]["last_run"] is None

    run = client.post(f"/api/jobs/{job_id}/run", headers=HEADERS)
    assert run.status_code == 200
    run_body = run.json()

    listed = client.get("/api/jobs")
    assert listed.status_code == 200
    last_run = listed.json()[0]["last_run"]
    assert last_run is not None
    assert last_run["id"] == run_body["id"]
    assert last_run["status"] == run_body["status"]
    assert last_run["dry_run"] is True
    assert "matched" in last_run
    assert "added" in last_run
    assert "errors" in last_run

    get_resp = client.get(f"/api/jobs/{job_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["last_run"]["id"] == run_body["id"]


def test_schedule_preview(client: TestClient) -> None:
    _create_user_and_login(client)
    resp = client.post(
        "/api/jobs/schedule-preview",
        json={"cron": "0 3 * * *", "count": 5},
        headers=HEADERS,
    )
    assert resp.status_code == 200
    times = resp.json()["times"]
    assert len(times) == 5
    assert times[0].endswith("Z")


def test_schedule_preview_rejects_invalid_cron(client: TestClient) -> None:
    _create_user_and_login(client)
    resp = client.post(
        "/api/jobs/schedule-preview",
        json={"cron": "not-a-cron", "count": 5},
        headers=HEADERS,
    )
    assert resp.status_code == 422
