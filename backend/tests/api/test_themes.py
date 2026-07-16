"""Theme API tests (Phase 24)."""

from __future__ import annotations

from fastapi.testclient import TestClient

HEADERS = {"X-Requested-With": "XMLHttpRequest"}

SAMPLE_CSS = """\
/* @name: Ocean Night */
/* @id: ocean-night */
:root[data-ptb-theme="ocean-night"] {
  --mantine-color-dark-9: #0a1628;
  --ptb-body-gradient: linear-gradient(165deg, #0a1628 0%, #12263f 100%);
}
"""


def _login(client: TestClient) -> None:
    client.post(
        "/api/setup/user",
        json={"username": "nick", "email": "nick@example.com", "password": "supersecret"},
        headers=HEADERS,
    )
    client.post(
        "/api/auth/login",
        json={"username": "nick", "password": "supersecret"},
        headers=HEADERS,
    )


def test_list_themes_includes_builtins(client: TestClient) -> None:
    _login(client)
    resp = client.get("/api/themes")
    assert resp.status_code == 200
    body = resp.json()
    ids = {t["id"] for t in body}
    assert {"one-dark-pro", "cinema-night", "nord", "dracula"} <= ids
    assert all(t["source"] == "builtin" for t in body if t["id"] == "one-dark-pro")


def test_settings_default_ui_theme(client: TestClient) -> None:
    _login(client)
    resp = client.get("/api/settings")
    assert resp.status_code == 200
    assert resp.json()["ui_theme"] == "cinema-night"


def test_put_theme_and_upload_cycle(client: TestClient) -> None:
    _login(client)

    put = client.put(
        "/api/settings/theme",
        json={"theme_id": "nord"},
        headers=HEADERS,
    )
    assert put.status_code == 200
    assert put.json()["theme_id"] == "nord"
    assert client.get("/api/settings").json()["ui_theme"] == "nord"

    upload = client.post(
        "/api/themes",
        json={"css": SAMPLE_CSS, "filename": "ocean-night.css"},
        headers=HEADERS,
    )
    assert upload.status_code == 200
    assert upload.json() == {
        "id": "ocean-night",
        "name": "Ocean Night",
        "source": "custom",
    }

    listed = client.get("/api/themes").json()
    assert any(t["id"] == "ocean-night" and t["source"] == "custom" for t in listed)

    css = client.get("/api/themes/ocean-night/css")
    assert css.status_code == 200
    assert "Ocean Night" in css.text

    activate = client.put(
        "/api/settings/theme",
        json={"theme_id": "ocean-night"},
        headers=HEADERS,
    )
    assert activate.status_code == 200
    assert client.get("/api/settings").json()["ui_theme"] == "ocean-night"

    deleted = client.delete("/api/themes/ocean-night", headers=HEADERS)
    assert deleted.status_code == 204

    # Missing custom falls back on read.
    assert client.get("/api/settings").json()["ui_theme"] == "cinema-night"


def test_cannot_delete_builtin(client: TestClient) -> None:
    _login(client)
    resp = client.delete("/api/themes/one-dark-pro", headers=HEADERS)
    assert resp.status_code == 400


def test_upload_rejects_builtin_id(client: TestClient) -> None:
    _login(client)
    css = "/* @id: nord */\n/* @name: Fake */\n:root { --x: 1; }\n"
    resp = client.post(
        "/api/themes",
        json={"css": css, "filename": "nord.css"},
        headers=HEADERS,
    )
    assert resp.status_code == 400


def test_upload_rejects_oversize(client: TestClient) -> None:
    _login(client)
    huge = "/* @id: huge-theme */\n/* @name: Huge */\n" + ("a" * (65 * 1024))
    resp = client.post(
        "/api/themes",
        json={"css": huge},
        headers=HEADERS,
    )
    assert resp.status_code == 400


def test_put_unknown_theme(client: TestClient) -> None:
    _login(client)
    resp = client.put(
        "/api/settings/theme",
        json={"theme_id": "does-not-exist"},
        headers=HEADERS,
    )
    assert resp.status_code == 400


def test_themes_require_auth(client: TestClient) -> None:
    assert client.get("/api/themes").status_code == 401
