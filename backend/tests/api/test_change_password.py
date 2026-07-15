"""Password change API tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

HEADERS = {"X-Requested-With": "XMLHttpRequest"}


def _login(client: TestClient, password: str = "supersecret") -> None:
    client.post(
        "/api/setup/user",
        json={"username": "nick", "email": "nick@example.com", "password": "supersecret"},
        headers=HEADERS,
    )
    client.post(
        "/api/auth/login",
        json={"username": "nick", "password": password},
        headers=HEADERS,
    )


def test_change_password_success(client: TestClient) -> None:
    _login(client)
    resp = client.post(
        "/api/auth/change-password",
        json={"current_password": "supersecret", "new_password": "newsecret1"},
        headers=HEADERS,
    )
    assert resp.status_code == 204

    client.post("/api/auth/logout", headers=HEADERS)
    login = client.post(
        "/api/auth/login",
        json={"username": "nick", "password": "newsecret1"},
        headers=HEADERS,
    )
    assert login.status_code == 200


def test_change_password_rejects_wrong_current(client: TestClient) -> None:
    _login(client)
    resp = client.post(
        "/api/auth/change-password",
        json={"current_password": "wrong", "new_password": "newsecret1"},
        headers=HEADERS,
    )
    assert resp.status_code == 400
