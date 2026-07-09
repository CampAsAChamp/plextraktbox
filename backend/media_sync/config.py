"""Application configuration loaded from environment variables.

All settings are prefixed with ``MEDIA_SYNC_`` (e.g. ``MEDIA_SYNC_SECRET_KEY``).
The secret key is required in production; a dev default is provided only when
``MEDIA_SYNC_ENV=dev`` so local runs work without ceremony.
"""

from __future__ import annotations

import base64
import hashlib
from functools import lru_cache
from pathlib import Path

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="MEDIA_SYNC_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    env: str = Field(default="dev", description="dev | prod")
    secret_key: str = Field(
        default="",
        description="Signs session cookies and derives the Fernet token-encryption key.",
    )
    data_dir: Path = Field(default=Path("./data"), description="Directory for the SQLite DB and caches.")
    session_cookie: str = "media_sync_session"
    log_level: str = "INFO"

    @model_validator(mode="after")
    def _require_secret_in_prod(self) -> Settings:
        if not self.secret_key:
            if self.env == "prod":
                raise ValueError("MEDIA_SYNC_SECRET_KEY is required when MEDIA_SYNC_ENV=prod")
            # Deterministic dev-only key so encrypted data survives restarts locally.
            self.secret_key = "dev-insecure-secret-key-do-not-use-in-production"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        return self

    @property
    def db_path(self) -> Path:
        return self.data_dir / "media_sync.db"

    @property
    def database_url(self) -> str:
        return f"sqlite:///{self.db_path}"

    @property
    def fernet_key(self) -> bytes:
        """Derive a urlsafe-base64 32-byte Fernet key from the secret key."""
        digest = hashlib.sha256(self.secret_key.encode("utf-8")).digest()
        return base64.urlsafe_b64encode(digest)


@lru_cache
def get_settings() -> Settings:
    return Settings()
