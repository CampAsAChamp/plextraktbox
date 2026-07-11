"""Runs API tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from tests.api.test_jobs import HEADERS, _configure_connections, _create_user_and_login


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


def test_run_history_after_job_run(client: TestClient) -> None:
    import respx

    @respx.mock
    def _run() -> None:
        _create_user_and_login(client)
        _configure_connections(client)

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

        detail = client.get(f"/api/runs/{run_id}")
        assert detail.status_code == 200
        assert detail.json()["status"] == "success"

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

    _run()
