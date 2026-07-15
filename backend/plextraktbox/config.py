"""Application configuration loaded from environment variables.

The secret key is required in production; a local default is provided only when
``ENV=local`` so local runs work without ceremony.
"""

from __future__ import annotations

import base64
import hashlib
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    env: Literal["local", "prod"] = Field(default="local", description="local | prod")
    secret_key: str = Field(
        default="",
        description="Signs session cookies and derives the Fernet token-encryption key.",
    )
    data_dir: Path = Field(default=Path("./data"), description="Directory for the SQLite DB and caches.")
    session_cookie: str = "plextraktbox_session"
    log_level: str = "INFO"
    log_format: str = Field(
        default="auto",
        description="Log output format: auto (json in prod, console in local), json, or console.",
    )
    trakt_client_id: str = Field(
        default="",
        description="Trakt API application client ID (registered once by the app maintainer).",
    )
    trakt_client_secret: str = Field(
        default="",
        description="Trakt API application client secret.",
    )
    sync_run_delay_seconds: float = Field(
        default=0,
        ge=0,
        description="Local-only seconds to wait at run start (ENV=local) for live log testing.",
    )

    @model_validator(mode="after")
    def _require_secret_in_prod(self) -> Settings:
        if not self.secret_key:
            if self.env == "prod":
                raise ValueError("SECRET_KEY is required when ENV=prod")
            # Deterministic dev-only key so encrypted data survives restarts locally.
            self.secret_key = "dev-insecure-secret-key-do-not-use-in-production"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        return self

    @property
    def db_path(self) -> Path:
        return self.data_dir / "plextraktbox.db"

    @property
    def database_url(self) -> str:
        return f"sqlite:///{self.db_path}"

    @property
    def fernet_key(self) -> bytes:
        """Derive a urlsafe-base64 32-byte Fernet key from the secret key."""
        digest = hashlib.sha256(self.secret_key.encode("utf-8")).digest()
        return base64.urlsafe_b64encode(digest)

    def require_trakt_credentials(self) -> tuple[str, str]:
        """Return the server-level Trakt API app credentials."""
        if not self.trakt_client_id or not self.trakt_client_secret:
            raise ValueError("Trakt API app is not configured. Set TRAKT_CLIENT_ID and TRAKT_CLIENT_SECRET.")
        return self.trakt_client_id, self.trakt_client_secret

    @property
    def plex_client_identifier(self) -> str:
        """Stable Plex OAuth client identifier for this deployment."""
        from plextraktbox.clients.plex_client import plex_client_identifier

        return plex_client_identifier(self.secret_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()
