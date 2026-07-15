"""Persist Letterboxd CSV exports under ``{DATA_DIR}/caches/letterboxd/``."""

from __future__ import annotations

import json
import shutil
from datetime import UTC, datetime, timedelta
from pathlib import Path

from plextraktbox.clients.letterboxd_client import LetterboxdExport, download_export
from plextraktbox.config import get_settings
from plextraktbox.logging_setup import get_logger

log = get_logger(__name__)

META_NAME = "meta.json"
RATINGS_NAME = "ratings.csv"
WATCHLIST_NAME = "watchlist.csv"
DIARY_NAME = "diary.csv"


def export_cache_root() -> Path:
    path = get_settings().data_dir / "caches" / "letterboxd"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _cache_dir(connection_id: int) -> Path:
    path = export_cache_root() / str(connection_id)
    path.mkdir(parents=True, exist_ok=True)
    return path


def invalidate_export_cache(connection_id: int) -> bool:
    """Remove cached export files for a connection. Returns True if anything was removed."""
    path = export_cache_root() / str(connection_id)
    if not path.exists():
        return False
    shutil.rmtree(path, ignore_errors=True)
    log.info(
        "sync.cache.letterboxd_export.invalidated",
        message=f"Cleared Letterboxd export cache for connection {connection_id}",
        connection_id=connection_id,
    )
    return True


def clear_all_export_caches() -> int:
    """Remove all Letterboxd export caches. Returns number of connection dirs removed."""
    root = export_cache_root()
    removed = 0
    for child in list(root.iterdir()):
        if child.is_dir():
            shutil.rmtree(child, ignore_errors=True)
            removed += 1
    return removed


def _read_cached(connection_id: int, username: str, ttl_hours: int) -> LetterboxdExport | None:
    directory = _cache_dir(connection_id)
    meta_path = directory / META_NAME
    if not meta_path.is_file():
        return None
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except OSError, json.JSONDecodeError:
        return None
    if not isinstance(meta, dict):
        return None
    if str(meta.get("username", "")) != username:
        return None
    fetched_raw = meta.get("fetched_at")
    if not isinstance(fetched_raw, str):
        return None
    try:
        fetched_at = datetime.fromisoformat(fetched_raw)
    except ValueError:
        return None
    if fetched_at.tzinfo is None:
        fetched_at = fetched_at.replace(tzinfo=UTC)
    if datetime.now(UTC) - fetched_at > timedelta(hours=ttl_hours):
        return None

    def _optional_csv(name: str) -> str | None:
        path = directory / name
        if not path.is_file():
            return None
        text = path.read_text(encoding="utf-8")
        return text if text.strip() else None

    return LetterboxdExport(
        ratings_csv=_optional_csv(RATINGS_NAME),
        watchlist_csv=_optional_csv(WATCHLIST_NAME),
        diary_csv=_optional_csv(DIARY_NAME),
    )


def _write_cached(connection_id: int, username: str, export: LetterboxdExport) -> None:
    directory = _cache_dir(connection_id)
    meta = {
        "username": username,
        "fetched_at": datetime.now(UTC).isoformat(),
    }
    (directory / META_NAME).write_text(json.dumps(meta), encoding="utf-8")
    for name, payload in (
        (RATINGS_NAME, export.ratings_csv),
        (WATCHLIST_NAME, export.watchlist_csv),
        (DIARY_NAME, export.diary_csv),
    ):
        path = directory / name
        if payload is None:
            path.unlink(missing_ok=True)
        else:
            path.write_text(payload, encoding="utf-8")


def get_or_download_export(
    *,
    connection_id: int,
    username: str,
    password: str,
    ttl_hours: int,
    force: bool = False,
) -> tuple[LetterboxdExport, str]:
    """Return ``(export, cache_status)`` where status is ``hit``, ``miss``, or ``forced``.

    Downloads on miss / expiry / force and writes through to disk.
    """
    if not force:
        cached = _read_cached(connection_id, username, ttl_hours)
        if cached is not None:
            log.info(
                "sync.cache.letterboxd_export.hit",
                message="Letterboxd export cache hit",
                connection_id=connection_id,
                ttl_hours=ttl_hours,
            )
            return cached, "hit"

    status = "forced" if force else "miss"
    log.info(
        f"sync.cache.letterboxd_export.{status}",
        message=(
            "Downloading Letterboxd export " + ("(force refresh)" if force else "(cache miss or expired)")
        ),
        connection_id=connection_id,
        ttl_hours=ttl_hours,
    )
    export = download_export(username, password)
    _write_cached(connection_id, username, export)
    return export, status
