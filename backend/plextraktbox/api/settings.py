"""Application settings and SQLite backup endpoints."""

from __future__ import annotations

import contextlib
import os
import sqlite3
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

from plextraktbox.api.deps import CurrentUserDep, SessionDep, require_csrf
from plextraktbox.config import get_settings
from plextraktbox.scheduler import get_scheduler_manager
from plextraktbox.schemas.settings import SettingsResponse, SettingsUpdateRequest
from plextraktbox.schemas.themes import ThemeActiveResponse, ThemeUpdateRequest
from plextraktbox.services import settings as settings_svc

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
