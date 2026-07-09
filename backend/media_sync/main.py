"""FastAPI application factory.

Serves the JSON API under ``/api`` and the built React SPA (when present) from
``media_sync/static``. In production the multi-stage Docker build copies the
Vite ``dist/`` output into that directory so a single container serves both.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from media_sync.api import health
from media_sync.config import get_settings
from media_sync.db import init_db
from media_sync.logging_setup import configure_logging, get_logger

STATIC_DIR = Path(__file__).parent / "static"

log = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    configure_logging()
    init_db()
    log.info("media_sync.startup", env=get_settings().env)
    # Scheduler is started here in Phase 4.
    yield
    log.info("media_sync.shutdown")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="media-sync", version="0.1.0", lifespan=lifespan)

    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.secret_key,
        session_cookie=settings.session_cookie,
        https_only=settings.env == "prod",
        same_site="lax",
    )

    # --- API routers (all under /api) ---
    app.include_router(health.router, prefix="/api")

    # --- SPA static hosting ---
    _mount_spa(app)

    return app


def _mount_spa(app: FastAPI) -> None:
    """Serve the built SPA, falling back to index.html for client-side routes."""
    if not STATIC_DIR.exists():

        @app.get("/")
        def _no_spa() -> JSONResponse:
            return JSONResponse(
                {"detail": "SPA not built. Run the frontend dev server or build it into static/."},
                status_code=200,
            )

        return

    assets = STATIC_DIR / "assets"
    if assets.exists():
        app.mount("/assets", StaticFiles(directory=assets), name="assets")

    index = STATIC_DIR / "index.html"

    @app.get("/{full_path:path}")
    def spa_fallback(full_path: str) -> FileResponse:
        # API 404s are handled by the routers above; anything else serves the SPA
        # so React Router can resolve the route.
        candidate = STATIC_DIR / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(index)


app = create_app()
