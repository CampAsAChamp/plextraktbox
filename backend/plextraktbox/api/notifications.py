"""Notification configuration and in-app notification endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from plextraktbox.api.deps import CurrentUserDep, SessionDep, require_csrf
from plextraktbox.models.inapp_notification import InAppNotification
from plextraktbox.models.notification_config import NotificationScope
from plextraktbox.notifications.dispatcher import (
    list_inapp_notifications,
    send_test_notification,
    unread_inapp_count,
)
from plextraktbox.schemas.notification import (
    InAppListResponse,
    InAppNotificationResponse,
    NotificationConfigCreateRequest,
    NotificationConfigResponse,
    NotificationConfigUpdateRequest,
    NotificationTestResponse,
    UnreadCountResponse,
)
from plextraktbox.services import notifications as notification_svc

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/configs", response_model=list[NotificationConfigResponse])
def list_notification_configs(
    _user: CurrentUserDep,
    session: SessionDep,
    job_id: int | None = None,
) -> list[NotificationConfigResponse]:
    if job_id is None:
        configs = notification_svc.list_configs(session)
    else:
        configs = notification_svc.list_configs(
            session,
            scope=NotificationScope.JOB,
            job_id=job_id,
        )
    return [NotificationConfigResponse.from_model(config) for config in configs]


@router.post(
    "/configs",
    response_model=NotificationConfigResponse,
    dependencies=[Depends(require_csrf)],
)
def create_notification_config(
    body: NotificationConfigCreateRequest,
    _user: CurrentUserDep,
    session: SessionDep,
) -> NotificationConfigResponse:
    try:
        config = notification_svc.create_config(session, body)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return NotificationConfigResponse.from_model(config)


@router.put(
    "/configs/{config_id}",
    response_model=NotificationConfigResponse,
    dependencies=[Depends(require_csrf)],
)
def update_notification_config(
    config_id: int,
    body: NotificationConfigUpdateRequest,
    _user: CurrentUserDep,
    session: SessionDep,
) -> NotificationConfigResponse:
    config = notification_svc.get_config(session, config_id)
    if config is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Config not found")
    config = notification_svc.update_config(session, config, body)
    return NotificationConfigResponse.from_model(config)


@router.delete(
    "/configs/{config_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_csrf)],
)
def delete_notification_config(
    config_id: int,
    _user: CurrentUserDep,
    session: SessionDep,
) -> None:
    config = notification_svc.get_config(session, config_id)
    if config is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Config not found")
    notification_svc.delete_config(session, config)


@router.post(
    "/configs/{config_id}/test",
    response_model=NotificationTestResponse,
    dependencies=[Depends(require_csrf)],
)
async def test_notification_config(
    config_id: int,
    _user: CurrentUserDep,
    session: SessionDep,
) -> NotificationTestResponse:
    config = notification_svc.get_config(session, config_id)
    if config is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Config not found")
    try:
        await send_test_notification(session, config)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return NotificationTestResponse(ok=True, message="Test notification sent")


@router.get("/inapp", response_model=InAppListResponse)
def list_inapp(
    _user: CurrentUserDep,
    session: SessionDep,
    limit: int = Query(default=50, ge=1, le=200),
    unread_only: bool = False,
) -> InAppListResponse:
    items = list_inapp_notifications(session, limit=limit, unread_only=unread_only)
    return InAppListResponse(
        items=[InAppNotificationResponse.from_model(item) for item in items],
        unread_count=unread_inapp_count(session),
    )


@router.get("/inapp/unread-count", response_model=UnreadCountResponse)
def get_unread_count(_user: CurrentUserDep, session: SessionDep) -> UnreadCountResponse:
    return UnreadCountResponse(unread_count=unread_inapp_count(session))


@router.post(
    "/inapp/{notification_id}/read",
    response_model=InAppNotificationResponse,
    dependencies=[Depends(require_csrf)],
)
def mark_inapp_read(
    notification_id: int,
    _user: CurrentUserDep,
    session: SessionDep,
) -> InAppNotificationResponse:
    row = session.get(InAppNotification, notification_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    row.read = True
    session.add(row)
    session.commit()
    session.refresh(row)
    return InAppNotificationResponse.from_model(row)


@router.post(
    "/inapp/read-all",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_csrf)],
)
def mark_all_inapp_read(_user: CurrentUserDep, session: SessionDep) -> None:
    rows = list_inapp_notifications(session, limit=500, unread_only=True)
    for row in rows:
        row.read = True
        session.add(row)
    session.commit()
