"""Shared pytest fixtures.

Each test gets an app backed by a throwaway SQLite file so the schema is created
fresh and nothing leaks between tests.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from sqlmodel import Session

# Configure settings BEFORE importing the app so get_settings() caches test values.
os.environ.setdefault("ENV", "dev")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("TRAKT_CLIENT_ID", "cid")
os.environ.setdefault("TRAKT_CLIENT_SECRET", "secret")


@pytest.fixture
def session(client: TestClient) -> Iterator[Session]:  # noqa: F821
    from plextraktbox.db import engine

    with Session(engine) as db_session:
        yield db_session


@pytest.fixture
def client(tmp_path: Path) -> Iterator[TestClient]:  # noqa: F821
    os.environ["DATA_DIR"] = str(tmp_path)

    # Reset the cached settings + engine so they pick up the tmp data dir.
    from plextraktbox import config, db

    config.get_settings.cache_clear()
    db._settings = config.get_settings()
    db.engine = db.create_engine(
        db._settings.database_url,
        echo=False,
        connect_args={"check_same_thread": False},
    )

    from fastapi.testclient import TestClient

    from plextraktbox.main import create_app
    import plextraktbox.scheduler.manager as scheduler_manager_mod

    scheduler_manager_mod._manager = None

    app = create_app()
    with TestClient(app) as c:
        yield c
