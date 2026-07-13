"""Health check endpoint (unauthenticated)."""

from __future__ import annotations

from fastapi import APIRouter

from plextraktbox.schemas.health import HealthResponse
from plextraktbox.version_info import __version__, built_at, git_sha

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> HealthResponse:
    return HealthResponse(
        version=__version__,
        git_sha=git_sha(),
        built_at=built_at(),
    )
