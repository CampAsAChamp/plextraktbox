"""Dev-only helpers (not registered in production)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from plextraktbox.api.deps import CurrentUserDep, SessionDep, require_csrf
from plextraktbox.models.inapp_notification import InAppLevel, InAppNotification
from plextraktbox.notifications.dispatcher import unread_inapp_count
from plextraktbox.schemas.notification import InAppListResponse, InAppNotificationResponse

router = APIRouter(tags=["dev"])

_SEED_NOTIFICATIONS: tuple[tuple[InAppLevel, str, str], ...] = (
    (
        InAppLevel.SUCCESS,
        "Watchlist sync finished",
        "Synced 12 items from Plex → Trakt (dry-run off).",
    ),
    (
        InAppLevel.INFO,
        "Ratings sync finished",
        "Pushed 3 Letterboxd ratings to Plex and Trakt.",
    ),
    (
        InAppLevel.WARNING,
        "Partial watched sync",
        "Marked 8 items watched in Plex; 1 title could not be matched.",
    ),
    (
        InAppLevel.ERROR,
        "Trakt connection needs re-auth",
        "Token refresh failed. Reconnect Trakt under Connections to resume syncs.",
    ),
)


@router.get("/revision")
def revision(request: Request) -> dict[str, float]:
    """Return the backend process start time so the dev landing page can auto-reload."""
    return {"started_at": request.app.state.started_at}


@router.post(
    "/notifications/seed",
    response_model=InAppListResponse,
    dependencies=[Depends(require_csrf)],
)
def seed_notifications(_user: CurrentUserDep, session: SessionDep) -> InAppListResponse:
    """Insert sample in-app notifications for local UI testing."""
    rows: list[InAppNotification] = []
    for level, title, body in _SEED_NOTIFICATIONS:
        row = InAppNotification(level=level, title=title, body=body, read=False)
        session.add(row)
        rows.append(row)
    session.commit()
    for row in rows:
        session.refresh(row)
    return InAppListResponse(
        items=[InAppNotificationResponse.from_model(row) for row in reversed(rows)],
        unread_count=unread_inapp_count(session),
    )
