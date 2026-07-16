"""Settings API tests."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient
from sqlmodel import Session

HEADERS = {"X-Requested-With": "XMLHttpRequest"}


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


def test_settings_requires_auth(client: TestClient) -> None:
    assert client.get("/api/settings").status_code == 401


def test_get_and_put_settings(client: TestClient) -> None:
    _login(client)
    got = client.get("/api/settings")
    assert got.status_code == 200
    body = got.json()
    assert body["global_dry_run"] is True
    assert body["log_retention_days"] == 30
    assert body["letterboxd_export_cache_ttl_hours"] == 24
    assert body["trakt_list_cache_ttl_minutes"] == 30

    assert body["cron_timezone"] == "UTC"

    put = client.put(
        "/api/settings",
        json={
            "default_cron": "15 2 * * *",
            "cron_timezone": "America/Los_Angeles",
            "log_retention_days": 7,
            "global_dry_run": False,
            "exclude_ids": {"tmdb": ["99"], "imdb": [], "tvdb": []},
            "letterboxd_export_cache_ttl_hours": 12,
            "trakt_list_cache_ttl_minutes": 45,
        },
        headers=HEADERS,
    )
    assert put.status_code == 200
    assert put.json()["default_cron"] == "15 2 * * *"
    assert put.json()["cron_timezone"] == "America/Los_Angeles"
    assert put.json()["cron_timezone_resolved"] == "America/Los_Angeles"
    assert put.json()["global_dry_run"] is False
    assert put.json()["exclude_ids"]["tmdb"] == ["99"]
    assert put.json()["letterboxd_export_cache_ttl_hours"] == 12
    assert put.json()["trakt_list_cache_ttl_minutes"] == 45

    local = client.put(
        "/api/settings",
        json={
            "default_cron": "15 2 * * *",
            "cron_timezone": "local",
            "cron_local_zone": "America/Denver",
            "log_retention_days": 7,
            "global_dry_run": False,
            "exclude_ids": {"tmdb": ["99"], "imdb": [], "tvdb": []},
            "letterboxd_export_cache_ttl_hours": 12,
            "trakt_list_cache_ttl_minutes": 45,
        },
        headers=HEADERS,
    )
    assert local.status_code == 200
    assert local.json()["cron_timezone"] == "local"
    assert local.json()["cron_timezone_resolved"] == "America/Denver"


def test_clear_sync_caches(client: TestClient) -> None:
    _login(client)
    resp = client.post(
        "/api/settings/clear-sync-caches",
        json={
            "letterboxd_export": True,
            "letterboxd_slug": True,
            "trakt_lists": True,
            "discover_keys": True,
        },
        headers=HEADERS,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["letterboxd_export"] == 0
    assert body["letterboxd_slug"] == 0
    assert body["trakt_lists"] == 0
    assert body["discover_keys"] == 0


def test_put_settings_validates_cron(client: TestClient) -> None:
    _login(client)
    resp = client.put(
        "/api/settings",
        json={
            "default_cron": "not-a-cron",
            "cron_timezone": "UTC",
            "log_retention_days": 7,
            "global_dry_run": True,
            "exclude_ids": {"tmdb": [], "imdb": [], "tvdb": []},
        },
        headers=HEADERS,
    )
    assert resp.status_code == 422


def test_put_settings_validates_cron_timezone(client: TestClient) -> None:
    _login(client)
    resp = client.put(
        "/api/settings",
        json={
            "default_cron": "0 3 * * *",
            "cron_timezone": "Not/A_Zone",
            "log_retention_days": 7,
            "global_dry_run": True,
            "exclude_ids": {"tmdb": [], "imdb": [], "tvdb": []},
        },
        headers=HEADERS,
    )
    assert resp.status_code == 422


def test_backup_download(client: TestClient) -> None:
    _login(client)
    resp = client.get("/api/settings/backup")
    assert resp.status_code == 200
    assert "sqlite" in resp.headers.get("content-type", "").lower() or resp.headers.get(
        "content-disposition", ""
    )
    assert len(resp.content) > 0
    assert resp.content.startswith(b"SQLite format 3")


def test_backup_restore_roundtrip(client: TestClient, tmp_path: Path) -> None:
    _login(client)
    download = client.get("/api/settings/backup")
    assert download.status_code == 200

    backup_file = tmp_path / "restore.db"
    backup_file.write_bytes(download.content)

    restore = client.post(
        "/api/settings/backup/restore",
        files={"file": ("restore.db", backup_file.read_bytes(), "application/x-sqlite3")},
        headers=HEADERS,
    )
    assert restore.status_code == 200
    assert restore.json()["ok"] is True

    me = client.get("/api/auth/me")
    assert me.status_code == 200
    assert me.json()["username"] == "nick"


def test_backup_restore_rejects_garbage(client: TestClient) -> None:
    _login(client)
    resp = client.post(
        "/api/settings/backup/restore",
        files={"file": ("bad.db", b"not-a-database", "application/octet-stream")},
        headers=HEADERS,
    )
    assert resp.status_code == 400


def test_backup_restore_rejects_incomplete_sqlite(client: TestClient, tmp_path: Path) -> None:
    import sqlite3

    _login(client)
    empty = tmp_path / "empty.db"
    sqlite3.connect(empty).close()
    resp = client.post(
        "/api/settings/backup/restore",
        files={"file": ("empty.db", empty.read_bytes(), "application/x-sqlite3")},
        headers=HEADERS,
    )
    assert resp.status_code == 400
    assert "required tables" in resp.json()["detail"].lower()


def test_backup_restore_rejects_while_run_active(client: TestClient, session: Session) -> None:
    from plextraktbox.models.job import Job, SourcePair
    from plextraktbox.models.job_run import JobRun, JobRunStatus, RunTrigger

    _login(client)
    job = Job(name="active", source_pair=SourcePair.PLEX_TRAKT, dry_run=True)
    session.add(job)
    session.commit()
    session.refresh(job)
    run = JobRun(job_id=job.id or 0, status=JobRunStatus.RUNNING, trigger=RunTrigger.MANUAL)
    session.add(run)
    session.commit()

    download = client.get("/api/settings/backup")
    assert download.status_code == 200

    resp = client.post(
        "/api/settings/backup/restore",
        files={"file": ("restore.db", download.content, "application/x-sqlite3")},
        headers=HEADERS,
    )
    assert resp.status_code == 409
