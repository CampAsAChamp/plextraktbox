"""Notifications API tests."""

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


def test_notification_configs_require_auth(client: TestClient) -> None:
    resp = client.get("/api/notifications/configs")
    assert resp.status_code == 401


def test_create_inapp_config_and_test(client: TestClient) -> None:
    _create_user_and_login(client)

    create = client.post(
        "/api/notifications/configs",
        json={
            "channel": "inapp",
            "enabled": True,
            "on_success": True,
            "on_failure": True,
            "scope": "global",
        },
        headers=HEADERS,
    )
    assert create.status_code == 200
    config_id = create.json()["id"]

    test = client.post(f"/api/notifications/configs/{config_id}/test", headers=HEADERS)
    assert test.status_code == 200
    assert test.json()["ok"] is True

    inapp = client.get("/api/notifications/inapp")
    assert inapp.status_code == 200
    body = inapp.json()
    assert body["unread_count"] >= 1
    assert len(body["items"]) >= 1


@respx.mock
def test_create_discord_config_and_test(client: TestClient) -> None:
    _create_user_and_login(client)
    route = respx.post("https://discord.test/webhook").mock(return_value=httpx.Response(204))

    create = client.post(
        "/api/notifications/configs",
        json={
            "channel": "discord",
            "enabled": True,
            "on_success": True,
            "on_failure": True,
            "scope": "global",
            "discord": {"webhook_url": "https://discord.test/webhook"},
        },
        headers=HEADERS,
    )
    assert create.status_code == 200
    config_id = create.json()["id"]
    assert create.json()["has_secret"] is True
    assert "webhook_url" not in create.json()["config"]

    test = client.post(f"/api/notifications/configs/{config_id}/test", headers=HEADERS)
    assert test.status_code == 200
    assert route.called


def test_mark_inapp_read(client: TestClient) -> None:
    _create_user_and_login(client)
    create = client.post(
        "/api/notifications/configs",
        json={"channel": "inapp", "scope": "global"},
        headers=HEADERS,
    )
    config_id = create.json()["id"]
    client.post(f"/api/notifications/configs/{config_id}/test", headers=HEADERS)

    unread = client.get("/api/notifications/inapp/unread-count")
    assert unread.json()["unread_count"] >= 1

    items = client.get("/api/notifications/inapp").json()["items"]
    notification_id = items[0]["id"]
    read = client.post(f"/api/notifications/inapp/{notification_id}/read", headers=HEADERS)
    assert read.status_code == 200
    assert read.json()["read"] is True

    mark_all = client.post("/api/notifications/inapp/read-all", headers=HEADERS)
    assert mark_all.status_code == 204
    assert client.get("/api/notifications/inapp/unread-count").json()["unread_count"] == 0


def test_delete_inapp_notification(client: TestClient) -> None:
    _create_user_and_login(client)
    create = client.post(
        "/api/notifications/configs",
        json={"channel": "inapp", "scope": "global"},
        headers=HEADERS,
    )
    config_id = create.json()["id"]
    client.post(f"/api/notifications/configs/{config_id}/test", headers=HEADERS)

    items = client.get("/api/notifications/inapp").json()["items"]
    notification_id = items[0]["id"]

    deleted = client.delete(f"/api/notifications/inapp/{notification_id}", headers=HEADERS)
    assert deleted.status_code == 204

    remaining_ids = [item["id"] for item in client.get("/api/notifications/inapp").json()["items"]]
    assert notification_id not in remaining_ids

    missing = client.delete(f"/api/notifications/inapp/{notification_id}", headers=HEADERS)
    assert missing.status_code == 404


def test_clear_all_inapp_notifications(client: TestClient) -> None:
    _create_user_and_login(client)
    create = client.post(
        "/api/notifications/configs",
        json={"channel": "inapp", "scope": "global"},
        headers=HEADERS,
    )
    config_id = create.json()["id"]
    client.post(f"/api/notifications/configs/{config_id}/test", headers=HEADERS)
    client.post(f"/api/notifications/configs/{config_id}/test", headers=HEADERS)

    items = client.get("/api/notifications/inapp").json()["items"]
    assert len(items) >= 2

    cleared = client.delete("/api/notifications/inapp/clear-all", headers=HEADERS)
    assert cleared.status_code == 204

    remaining = client.get("/api/notifications/inapp").json()
    assert remaining["items"] == []
    assert remaining["unread_count"] == 0
    assert client.get("/api/notifications/inapp/unread-count").json()["unread_count"] == 0


def test_dev_seed_notifications(client: TestClient) -> None:
    _create_user_and_login(client)

    seeded = client.post("/api/dev/notifications/seed", headers=HEADERS)
    assert seeded.status_code == 200
    body = seeded.json()
    assert len(body["items"]) == 4
    assert body["unread_count"] >= 4
    levels = {item["level"] for item in body["items"]}
    assert levels == {"info", "success", "warning", "error"}

    listed = client.get("/api/notifications/inapp").json()
    assert listed["unread_count"] >= 4
    assert len(listed["items"]) >= 4


def test_dev_seed_notifications_requires_auth(client: TestClient) -> None:
    resp = client.post("/api/dev/notifications/seed", headers=HEADERS)
    assert resp.status_code == 401
