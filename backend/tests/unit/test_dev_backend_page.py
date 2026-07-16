"""Dev backend landing page."""

from __future__ import annotations

from fastapi.testclient import TestClient

from plextraktbox import config
from plextraktbox.main import create_app


def test_dev_root_serves_styled_landing_page(monkeypatch) -> None:
    monkeypatch.setenv("ENV", "local")
    config.get_settings.cache_clear()
    client = TestClient(create_app())

    response = client.get("/")

    assert response.status_code == 200
    assert "plextraktbox — dev backend" in response.text
    assert "Check API status" in response.text
    assert "/api/health" in response.text
    assert response.headers["cache-control"] == "no-store"


def test_dev_revision_endpoint(monkeypatch) -> None:
    monkeypatch.setenv("ENV", "local")
    config.get_settings.cache_clear()
    with TestClient(create_app()) as client:
        response = client.get("/api/dev/revision")

    assert response.status_code == 200
    assert isinstance(response.json()["started_at"], float)


def test_dev_revision_not_registered_in_prod(monkeypatch) -> None:
    monkeypatch.setenv("ENV", "prod")
    config.get_settings.cache_clear()
    app = create_app()

    assert "/api/dev/revision" not in app.openapi()["paths"]
    assert "/api/dev/notifications/seed" not in app.openapi()["paths"]
