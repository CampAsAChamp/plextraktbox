"""FastAPI application factory.

Serves the JSON API under ``/api`` and the built React SPA (when present) from
``plextraktbox/static``. In production the multi-stage Docker build copies the
Vite ``dist/`` output into that directory so a single container serves both.
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from plextraktbox.api import auth, connections, dev, health, jobs, notifications, run_logs, runs, setup
from plextraktbox.config import get_settings
from plextraktbox.db import init_db
from plextraktbox.dev_backend_page import DEV_BACKEND_HTML
from plextraktbox.http_access import AccessLogMiddleware
from plextraktbox.logging_setup import configure_logging, get_logger
from plextraktbox.logstream import get_log_hub, get_log_writer
from plextraktbox.scheduler import get_scheduler_manager
from plextraktbox.version_info import __version__

STATIC_DIR = Path(__file__).parent / "static"

log = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    configure_logging()
    init_db()
    get_log_writer().start()
    get_log_hub().set_event_loop(asyncio.get_running_loop())
    scheduler = get_scheduler_manager()
    scheduler.start()
    app.state.scheduler = scheduler
    app.state.started_at = time.time()
    log.info("plextraktbox.startup", env=get_settings().env)
    yield
    scheduler.shutdown(wait=True)
    get_log_writer().stop()
    log.info("plextraktbox.shutdown")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="plextraktbox", version=__version__, lifespan=lifespan)

    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.secret_key,
        session_cookie=settings.session_cookie,
        https_only=settings.env == "prod",
        same_site="lax",
    )
    app.add_middleware(AccessLogMiddleware)

    # --- API routers (all under /api) ---
    app.include_router(health.router, prefix="/api")
    app.include_router(setup.router, prefix="/api")
    app.include_router(auth.router, prefix="/api")
    app.include_router(connections.router, prefix="/api")
    app.include_router(jobs.router, prefix="/api")
    app.include_router(runs.router, prefix="/api")
    app.include_router(run_logs.router, prefix="/api")
    app.include_router(notifications.router, prefix="/api")

    if settings.env == "dev":
        app.include_router(dev.router, prefix="/api/dev")

    # --- SPA static hosting ---
    _mount_spa(app)

    return app


def _mount_spa(app: FastAPI) -> None:
    """Serve the built SPA, falling back to index.html for client-side routes."""
    settings = get_settings()
    if settings.env == "dev":

        @app.get("/{full_path:path}")
        def _dev_ui_notice(full_path: str) -> HTMLResponse:
            return HTMLResponse(
                DEV_BACKEND_HTML,
                headers={"Cache-Control": "no-store"},
            )

        return

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
