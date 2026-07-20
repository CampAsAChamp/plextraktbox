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
    wait_for_run,
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
    assert run.json()["status"] == "running"
    finished = wait_for_run(client, run_id)
    assert finished["status"] == "success"

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
    assert after_delete.json()["items"][0]["source_pair"] == "plex_trakt"


def test_list_runs_with_unmatched_summary(client: TestClient) -> None:
    """Runs with nested unmatched identifiers must serialize without ValidationError."""
    _create_user_and_login(client)

    from plextraktbox.sync.plans import RunSummary, UnmatchedItem

    summary = RunSummary(
        matched=1,
        planned=2,
        unmatched=[
            UnmatchedItem(
                source="plex",
                data_type="watchlist",
                title="Some Movie",
                source_key="plex:1",
                reason="no match",
                identifiers={"tmdb": "123"},
            ),
            UnmatchedItem(
                source="trakt",
                data_type="watchlist",
                title="Other Movie",
                source_key="trakt:2",
                reason="no match",
                identifiers={},
            ),
        ],
    )

    with Session(db.engine) as session:
        run = JobRun(
            job_id=1,
            job_name="Unmatched run",
            trigger=RunTrigger.MANUAL,
            dry_run=True,
            status=JobRunStatus.PARTIAL,
            started_at=datetime.now(UTC),
            finished_at=datetime.now(UTC),
        )
        run.set_summary(summary)
        session.add(run)
        session.commit()
        session.refresh(run)
        run_id = run.id
        assert run_id is not None

    list_resp = client.get("/api/runs")
    assert list_resp.status_code == 200
    items = list_resp.json()["items"]
    assert len(items) == 1
    assert items[0]["id"] == run_id
    assert items[0]["summary"]["unmatched_count"] == 2
    assert items[0]["summary"]["unmatched"][0]["identifiers"] == {"tmdb": "123"}
    assert items[0]["summary"]["unmatched"][1]["identifiers"] == {}

    detail = client.get(f"/api/runs/{run_id}")
    assert detail.status_code == 200
    assert detail.json()["summary"]["unmatched_count"] == 2


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


def test_cancel_run(client: TestClient) -> None:
    _create_user_and_login(client)

    with Session(db.engine) as session:
        run = JobRun(
            job_id=1,
            job_name="Running job",
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

    from plextraktbox.sync.cancellation import register_cancel_event

    event = register_cancel_event(run_id)
    assert not event.is_set()

    resp = client.post(f"/api/runs/{run_id}/cancel", headers=HEADERS)
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "failed"
    assert body["error"] == "Cancelled by user"
    assert event.is_set()

    again = client.post(f"/api/runs/{run_id}/cancel", headers=HEADERS)
    assert again.status_code == 409
