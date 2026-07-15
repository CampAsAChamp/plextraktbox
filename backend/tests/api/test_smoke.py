"""API smoke: health → setup/login → list jobs (in-process TestClient)."""

from __future__ import annotations

from fastapi.testclient import TestClient

HEADERS = {"X-Requested-With": "XMLHttpRequest"}


def test_smoke_health_login_list_jobs(client: TestClient) -> None:
    health = client.get("/api/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"

    setup = client.post(
        "/api/setup/user",
        json={
            "username": "nick",
            "email": "nick@example.com",
            "password": "supersecret",
        },
        headers=HEADERS,
    )
    assert setup.status_code == 201

    login = client.post(
        "/api/auth/login",
        json={"username": "nick", "password": "supersecret"},
        headers=HEADERS,
    )
    assert login.status_code == 200
    assert "plextraktbox_session" in client.cookies

    jobs = client.get("/api/jobs")
    assert jobs.status_code == 200
    assert isinstance(jobs.json(), list)
