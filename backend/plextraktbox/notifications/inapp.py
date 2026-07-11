"""In-app notification persistence."""

from __future__ import annotations

from sqlmodel import Session

from plextraktbox.logging_setup import get_logger
from plextraktbox.models.inapp_notification import InAppLevel, InAppNotification
from plextraktbox.models.notification_config import NotificationConfig
from plextraktbox.notifications.payload import NotificationPayload

log = get_logger(__name__)

_LEVEL_BY_STATUS = {
    "success": InAppLevel.SUCCESS,
    "failed": InAppLevel.ERROR,
    "partial": InAppLevel.WARNING,
    "running": InAppLevel.INFO,
}


async def send_inapp(session: Session, config: NotificationConfig, payload: NotificationPayload) -> None:
    del config  # in-app channel has no per-config options today
    level = _LEVEL_BY_STATUS.get(payload.status, InAppLevel.INFO)
    row = InAppNotification(
        level=level,
        title=payload.title(),
        body=payload.body_text(),
        run_id=None if payload.run_id <= 0 else payload.run_id,
    )
    session.add(row)
    session.commit()
    log.info("notification.inapp.sent", run_id=payload.run_id, job_id=payload.job_id)
