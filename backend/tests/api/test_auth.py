"""Auth and setup API tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

HEADERS = {"X-Requested-With": "XMLHttpRequest"}


def _create_user(client: TestClient) -> dict[str, str | int]:
    resp = client.post(
        "/api/setup/user",
        json={
            "username": "nick",
            "email": "nick@example.com",
            "password": "supersecret",
        },
        headers=HEADERS,
    )
    assert resp.status_code == 201
    return resp.json()


def test_setup_status_before_user(client: TestClient) -> None:
    resp = client.get("/api/setup/status")
    assert resp.status_code == 200
    assert resp.json() == {"needs_setup": True}


def test_setup_user_creates_account(client: TestClient) -> None:
    data = _create_user(client)
    assert data["username"] == "nick"
    assert data["email"] == "nick@example.com"
    assert "id" in data


def test_setup_status_after_user(client: TestClient) -> None:
    _create_user(client)
    resp = client.get("/api/setup/status")
    assert resp.json() == {"needs_setup": False}


def test_setup_user_rejected_when_already_configured(client: TestClient) -> None:
    _create_user(client)
    resp = client.post(
        "/api/setup/user",
        json={
            "username": "other",
            "email": "other@example.com",
            "password": "anothersecret",
        },
        headers=HEADERS,
    )
    assert resp.status_code == 409


def test_setup_user_requires_csrf_header(client: TestClient) -> None:
    resp = client.post(
        "/api/setup/user",
        json={
            "username": "nick",
            "email": "nick@example.com",
            "password": "supersecret",
        },
    )
    assert resp.status_code == 400


def test_login_and_me(client: TestClient) -> None:
    _create_user(client)
    login = client.post(
        "/api/auth/login",
        json={"username": "nick", "password": "supersecret"},
        headers=HEADERS,
    )
    assert login.status_code == 200
    assert login.json()["username"] == "nick"
    assert login.json()["avatar_url"].endswith("484f70e21a3d3480e013519f8236bb86?s=80&d=identicon")

    me = client.get("/api/auth/me")
    assert me.status_code == 200
    assert me.json()["email"] == "nick@example.com"
    assert me.json()["avatar_url"].endswith("484f70e21a3d3480e013519f8236bb86?s=80&d=identicon")


def test_login_with_email(client: TestClient) -> None:
    _create_user(client)
    login = client.post(
        "/api/auth/login",
        json={"username": "nick@example.com", "password": "supersecret"},
        headers=HEADERS,
    )
    assert login.status_code == 200


def test_login_rejects_bad_password(client: TestClient) -> None:
    _create_user(client)
    resp = client.post(
        "/api/auth/login",
        json={"username": "nick", "password": "wrong"},
        headers=HEADERS,
    )
    assert resp.status_code == 401


def test_me_requires_session(client: TestClient) -> None:
    _create_user(client)
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401


def test_logout_clears_session(client: TestClient) -> None:
    _create_user(client)
    client.post(
        "/api/auth/login",
        json={"username": "nick", "password": "supersecret"},
        headers=HEADERS,
    )
    logout = client.post("/api/auth/logout", headers=HEADERS)
    assert logout.status_code == 204
    assert client.get("/api/auth/me").status_code == 401
