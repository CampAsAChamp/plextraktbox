"""Runs API tests."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
import respx
from fastapi.testclient import TestClient
from sqlmodel import Session

from plextraktbox import db
from plextraktbox.models.job_run import JobRun, JobRunStatus, RunTrigger
from tests.api.test_jobs import (
    HEADERS,
    _configure_connections,
    _create_user_and_login,
    _mock_live_fetch,
)


def test_runs_require_auth(client: TestClient) -> None:
    _create_user_and_login(client)
    client.post("/api/auth/logout", headers=HEADERS)
    resp = client.get("/api/runs")
    assert resp.status_code == 401


def test_list_runs_empty(client: TestClient) -> None:
    _create_user_and_login(client)
    resp = client.get("/api/runs")
    assert resp.status_code == 200
    body = resp.json()
    assert body["items"] == []
    assert body["limit"] == 50


def test_get_run_not_found(client: TestClient) -> None:
    _create_user_and_login(client)
    resp = client.get("/api/runs/999")
    assert resp.status_code == 404


@respx.mock
def test_run_history_after_job_run(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    _create_user_and_login(client)
    _configure_connections(client)
    _mock_live_fetch(monkeypatch)

    create = client.post(
        "/api/jobs",
        json={
            "name": "History test",
            "source_pair": "plex_trakt",
            "data_types": ["watchlist"],
            "dry_run": True,
        },
        headers=HEADERS,
    )
    job_id = create.json()["id"]

    run = client.post(f"/api/jobs/{job_id}/run", headers=HEADERS)
    assert run.status_code == 200
    run_id = run.json()["id"]

    list_resp = client.get("/api/runs")
    assert list_resp.status_code == 200
    items = list_resp.json()["items"]
    assert len(items) == 1
    assert items[0]["id"] == run_id
    assert items[0]["job_name"] == "History test"
    assert items[0]["source_pair"] == "plex_trakt"

    detail = client.get(f"/api/runs/{run_id}")
    assert detail.status_code == 200
    assert detail.json()["status"] == "success"
    assert detail.json()["source_pair"] == "plex_trakt"

    filtered = client.get(f"/api/runs?job_id={job_id}")
    assert filtered.status_code == 200
    assert len(filtered.json()["items"]) == 1

    delete = client.delete(f"/api/jobs/{job_id}", headers=HEADERS)
    assert delete.status_code == 204

    after_delete = client.get(f"/api/runs?job_id={job_id}")
    assert after_delete.status_code == 200
    assert len(after_delete.json()["items"]) == 1
    assert after_delete.json()["items"][0]["id"] == run_id
    assert after_delete.json()["items"][0]["job_name"] == "History test"
    assert after_delete.json()["items"][0]["source_pair"] is None


def test_mark_run_failed(client: TestClient) -> None:
    _create_user_and_login(client)

    with Session(db.engine) as session:
        run = JobRun(
            job_id=1,
            job_name="Stuck job",
            trigger=RunTrigger.MANUAL,
            dry_run=True,
            status=JobRunStatus.RUNNING,
            started_at=datetime.now(UTC),
        )
        session.add(run)
        session.commit()
        session.refresh(run)
        run_id = run.id
        assert run_id is not None

    resp = client.post(f"/api/runs/{run_id}/mark-failed", headers=HEADERS)
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == run_id
    assert body["status"] == "failed"
    assert body["error"] == "Marked as failed by user"
    assert body["finished_at"] is not None

    again = client.post(f"/api/runs/{run_id}/mark-failed", headers=HEADERS)
    assert again.status_code == 409


def test_mark_run_failed_not_found(client: TestClient) -> None:
    _create_user_and_login(client)
    resp = client.post("/api/runs/999/mark-failed", headers=HEADERS)
    assert resp.status_code == 404
