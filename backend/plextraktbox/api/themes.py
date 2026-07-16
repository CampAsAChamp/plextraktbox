"""UI theme list / upload / delete endpoints (Phase 24)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse

from plextraktbox.api.deps import CurrentUserDep, require_csrf
from plextraktbox.schemas.themes import ThemeInfoResponse, ThemeUploadRequest
from plextraktbox.services import themes as themes_svc

router = APIRouter(prefix="/themes", tags=["themes"])


def _to_response(info: themes_svc.ThemeInfo) -> ThemeInfoResponse:
    return ThemeInfoResponse(id=info.id, name=info.name, source=info.source, swatches=info.swatches)


@router.get("", response_model=list[ThemeInfoResponse])
def list_themes(_user: CurrentUserDep) -> list[ThemeInfoResponse]:
    return [_to_response(t) for t in themes_svc.list_themes()]


@router.post(
    "",
    response_model=ThemeInfoResponse,
    dependencies=[Depends(require_csrf)],
)
def upload_theme(body: ThemeUploadRequest, _user: CurrentUserDep) -> ThemeInfoResponse:
    try:
        info = themes_svc.save_custom_theme(body.css, filename=body.filename)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _to_response(info)


@router.get("/{theme_id}/css", response_class=PlainTextResponse)
def get_theme_css(theme_id: str, _user: CurrentUserDep) -> PlainTextResponse:
    if theme_id in themes_svc.BUILTIN_IDS:
        raise HTTPException(status_code=404, detail="built-in themes have no CSS payload")
    try:
        css = themes_svc.read_custom_css(theme_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="theme not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return PlainTextResponse(css, media_type="text/css; charset=utf-8")


@router.delete("/{theme_id}", status_code=204, dependencies=[Depends(require_csrf)])
def delete_theme(theme_id: str, _user: CurrentUserDep) -> None:
    try:
        themes_svc.delete_custom_theme(theme_id)
    except PermissionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="theme not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
