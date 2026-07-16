"""Application settings and SQLite backup endpoints."""

from __future__ import annotations

import contextlib
import os
import sqlite3
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from fastapi.responses import FileResponse
from sqlmodel import Session
from starlette.background import BackgroundTask

from plextraktbox import db
from plextraktbox.api.deps import CurrentUserDep, SessionDep, require_csrf
from plextraktbox.config import get_settings
from plextraktbox.models.user import User
from plextraktbox.scheduler import get_scheduler_manager
from plextraktbox.schemas.settings import (
    BackupRestoreResponse,
    ClearSyncCachesRequest,
    ClearSyncCachesResponse,
    ExcludeIds,
    SettingsResponse,
    SettingsUpdateRequest,
)
from plextraktbox.schemas.themes import ThemeActiveResponse, ThemeUpdateRequest
from plextraktbox.services import backup as backup_svc
from plextraktbox.services import settings as settings_svc
from plextraktbox.services import sync_caches as sync_caches_svc

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=SettingsResponse)
def get_settings_endpoint(_user: CurrentUserDep, session: SessionDep) -> SettingsResponse:
    app_settings = settings_svc.ensure_defaults(session)
    return SettingsResponse.from_app_settings(app_settings)


@router.put("", response_model=SettingsResponse, dependencies=[Depends(require_csrf)])
def update_settings_endpoint(
    body: SettingsUpdateRequest,
    _user: CurrentUserDep,
    session: SessionDep,
) -> SettingsResponse:
    settings_svc.ensure_defaults(session)
    previous = settings_svc.get_app_settings(session)
    updated = settings_svc.update_app_settings(session, body.to_app_settings())
    if previous.cron_timezone != updated.cron_timezone:
        # Re-register job triggers so hour/minute walls follow the new zone.
        get_scheduler_manager().load_all_jobs()
    return SettingsResponse.from_app_settings(updated)


@router.post(
    "/exclude-ids",
    response_model=SettingsResponse,
    dependencies=[Depends(require_csrf)],
)
def append_exclude_ids_endpoint(
    body: ExcludeIds,
    _user: CurrentUserDep,
    session: SessionDep,
) -> SettingsResponse:
    """Merge TMDB/IMDb/TVDB ids into the global exclude list."""
    settings_svc.ensure_defaults(session)
    updated = settings_svc.append_exclude_ids(
        session,
        {"tmdb": body.tmdb, "imdb": body.imdb, "tvdb": body.tvdb},
    )
    return SettingsResponse.from_app_settings(updated)


@router.put(
    "/theme",
    response_model=ThemeActiveResponse,
    dependencies=[Depends(require_csrf)],
)
def update_theme_endpoint(
    body: ThemeUpdateRequest,
    _user: CurrentUserDep,
    session: SessionDep,
) -> ThemeActiveResponse:
    settings_svc.ensure_defaults(session)
    try:
        theme_id = settings_svc.update_ui_theme(session, body.theme_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ThemeActiveResponse(theme_id=theme_id)


@router.post(
    "/clear-sync-caches",
    response_model=ClearSyncCachesResponse,
    dependencies=[Depends(require_csrf)],
)
def clear_sync_caches_endpoint(
    body: ClearSyncCachesRequest,
    _user: CurrentUserDep,
    session: SessionDep,
) -> ClearSyncCachesResponse:
    result = sync_caches_svc.clear_sync_caches(
        session,
        letterboxd_export=body.letterboxd_export,
        letterboxd_slug=body.letterboxd_slug,
        trakt_lists=body.trakt_lists,
        discover_keys=body.discover_keys,
    )
    return ClearSyncCachesResponse(
        letterboxd_export=result.letterboxd_export,
        letterboxd_slug=result.letterboxd_slug,
        trakt_lists=result.trakt_lists,
        discover_keys=result.discover_keys,
    )


def _unlink_quiet(path: Path) -> None:
    with contextlib.suppress(OSError):
        path.unlink(missing_ok=True)


@router.get("/backup")
def download_backup(_user: CurrentUserDep) -> FileResponse:
    """Stream a consistent SQLite snapshot of the application database."""
    db_path = get_settings().db_path
    fd, tmp_name = tempfile.mkstemp(prefix="plextraktbox-backup-", suffix=".db")
    os.close(fd)
    tmp_path = Path(tmp_name)

    source = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        dest = sqlite3.connect(tmp_path)
        try:
            source.backup(dest)
        finally:
            dest.close()
    finally:
        source.close()

    return FileResponse(
        path=tmp_path,
        filename="plextraktbox-backup.db",
        media_type="application/x-sqlite3",
        background=BackgroundTask(_unlink_quiet, tmp_path),
    )


def _require_user_id(request: Request) -> int:
    """Authenticate without holding a session open for the whole request.

    Restore disposes the SQLAlchemy engine mid-request, so ``CurrentUserDep`` /
    ``SessionDep`` must not keep a live session across the replace.
    """
    user_id = request.session.get("user_id")
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    with Session(db.engine) as session:
        user = session.get(User, user_id)
        if user is None:
            request.session.clear()
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
        return int(user.id) if user.id is not None else int(user_id)


@router.post(
    "/backup/restore",
    response_model=BackupRestoreResponse,
    dependencies=[Depends(require_csrf)],
)
async def restore_backup(
    request: Request,
    file: UploadFile = File(...),
) -> BackupRestoreResponse:
    """Replace the live database with an uploaded SQLite backup."""
    _require_user_id(request)

    suffix = Path(file.filename or "backup.db").suffix.lower()
    if suffix and suffix not in {".db", ".sqlite", ".sqlite3"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Upload a SQLite database file (.db)",
        )

    fd, tmp_name = tempfile.mkstemp(prefix="plextraktbox-restore-", suffix=".db")
    os.close(fd)
    tmp_path = Path(tmp_name)
    try:
        with tmp_path.open("wb") as out:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                out.write(chunk)

        try:
            backup_svc.restore_database(tmp_path)
        except backup_svc.BackupRestoreError as exc:
            raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    finally:
        _unlink_quiet(tmp_path)

    return BackupRestoreResponse()
