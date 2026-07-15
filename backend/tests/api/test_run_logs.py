"""Run log API tests."""

from __future__ import annotations

import json
import time

import pytest
import respx
from fastapi.testclient import TestClient

from tests.api.test_jobs import (
    HEADERS,
    _configure_connections,
    _create_user_and_login,
    _mock_live_fetch,
)


def _run_job_and_get_id(client: TestClient) -> int:
    create = client.post(
        "/api/jobs",
        json={
            "name": "Log test",
            "source_pair": "plex_trakt",
            "data_types": ["watchlist"],
            "dry_run": True,
        },
        headers=HEADERS,
    )
    job_id = create.json()["id"]
    run = client.post(f"/api/jobs/{job_id}/run", headers=HEADERS)
    assert run.status_code == 200
    return run.json()["id"]


def test_run_logs_require_auth(client: TestClient) -> None:
    _create_user_and_login(client)
    client.post("/api/auth/logout", headers=HEADERS)
    resp = client.get("/api/runs/1/logs")
    assert resp.status_code == 401


@respx.mock
def test_run_logs_after_job_run(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    _create_user_and_login(client)
    _configure_connections(client)
    _mock_live_fetch(monkeypatch)
    run_id = _run_job_and_get_id(client)

    deadline = time.monotonic() + 5
    items: list[dict] = []
    while time.monotonic() < deadline:
        resp = client.get(f"/api/runs/{run_id}/logs")
        assert resp.status_code == 200
        body = resp.json()
        items = body["items"]
        if items:
            break
        time.sleep(0.05)

    assert items, "expected persisted run logs"
    assert any("sync.run.complete" in item["message"] for item in items)

    filtered = client.get(f"/api/runs/{run_id}/logs?search=complete")
    assert filtered.status_code == 200
    assert len(filtered.json()["items"]) >= 1


@respx.mock
def test_run_logs_stream_completed_run(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    _create_user_and_login(client)
    _configure_connections(client)
    _mock_live_fetch(monkeypatch)
    run_id = _run_job_and_get_id(client)

    with client.stream("GET", f"/api/runs/{run_id}/logs/stream") as response:
        assert response.status_code == 200
        events: list[dict] = []
        for line in response.iter_lines():
            if not line.startswith("data:"):
                continue
            payload = json.loads(line.removeprefix("data:").strip())
            events.append(payload)
            if payload.get("type") == "end":
                break

    assert any(event.get("type") == "log" for event in events)
    assert events[-1]["type"] == "end"
    assert events[-1]["status"] in {"success", "partial", "failed"}


def test_run_logs_not_found(client: TestClient) -> None:
    _create_user_and_login(client)
    resp = client.get("/api/runs/999/logs")
    assert resp.status_code == 404


@respx.mock
def test_export_run_logs_txt_and_jsonl(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _create_user_and_login(client)
    _configure_connections(client)
    _mock_live_fetch(monkeypatch)
    run_id = _run_job_and_get_id(client)

    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        listed = client.get(f"/api/runs/{run_id}/logs")
        if listed.json()["items"]:
            break
        time.sleep(0.05)

    txt = client.get(f"/api/runs/{run_id}/logs/export?format=txt")
    assert txt.status_code == 200
    assert "attachment" in txt.headers["content-disposition"]
    assert f"run-{run_id}-logs.txt" in txt.headers["content-disposition"]
    assert "text/plain" in txt.headers["content-type"]
    assert "sync.run.complete" in txt.text

    jsonl = client.get(f"/api/runs/{run_id}/logs/export?format=jsonl")
    assert jsonl.status_code == 200
    assert f"run-{run_id}-logs.jsonl" in jsonl.headers["content-disposition"]
    lines = [line for line in jsonl.text.splitlines() if line.strip()]
    assert lines
    parsed = json.loads(lines[0])
    assert "message" in parsed
    assert "level" in parsed
    assert any("sync.run.complete" in json.loads(line)["message"] for line in lines)


def test_export_run_logs_not_found(client: TestClient) -> None:
    _create_user_and_login(client)
    resp = client.get("/api/runs/999/logs/export?format=txt")
    assert resp.status_code == 404
