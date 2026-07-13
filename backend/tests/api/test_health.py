"""Phase 0 smoke test: the app boots and the health endpoint responds."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from plextraktbox import __version__


def test_health_ok(client: TestClient) -> None:
    resp = client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["version"] == __version__
    assert body["git_sha"] is None
    assert body["built_at"] is None


def test_health_includes_build_metadata(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PLEXTRAKTBOX_GIT_SHA", "deadbeef")
    monkeypatch.setenv("PLEXTRAKTBOX_BUILD_TIME", "2026-07-13T04:00:00Z")
    resp = client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["git_sha"] == "deadbeef"
    assert body["built_at"] == "2026-07-13T04:00:00Z"
