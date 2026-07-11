"""Dev-only helpers (not registered in production)."""

from __future__ import annotations

from fastapi import APIRouter, Request

router = APIRouter(tags=["dev"])


@router.get("/revision")
def revision(request: Request) -> dict[str, float]:
    """Return the backend process start time so the dev landing page can auto-reload."""
    return {"started_at": request.app.state.started_at}
