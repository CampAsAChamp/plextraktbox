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
    session_https_only: bool | None = Field(
        default=None,
        description=(
            "Secure session cookie policy. "
            "Unset (default): auto — set Secure when the client uses HTTPS "
            "(including X-Forwarded-Proto from Cloudflare Tunnel), so LAN HTTP "
            "and HTTPS both work. "
            "true: always Secure (HTTPS-only). "
            "false: never Secure."
        ),
    )
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
    flaresolverr_url: str = Field(
        default="",
        description=(
            "Optional FlareSolverr base URL (e.g. http://192.168.1.105:30098). "
            "When set, Letterboxd session bootstrap clears Cloudflare via FlareSolverr."
        ),
    )
    flaresolverr_timeout_ms: int = Field(
        default=60_000,
        ge=1_000,
        description="FlareSolverr maxTimeout in milliseconds for challenge solves.",
    )

    @model_validator(mode="after")
    def _require_secret_in_prod(self) -> Settings:
        if not self.secret_key:
            if self.env == "prod":
                raise ValueError("SECRET_KEY is required when ENV=prod")
            # Deterministic dev-only key so encrypted data survives restarts locally.
            self.secret_key = "dev-insecure-secret-key-do-not-use-in-production"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.flaresolverr_url = self.flaresolverr_url.strip().rstrip("/")
        return self

    @property
    def session_https_only_mode(self) -> Literal["auto", "always", "never"]:
        """Resolved Secure-cookie policy for AdaptiveSessionMiddleware."""
        if self.session_https_only is True:
            return "always"
        if self.session_https_only is False:
            return "never"
        return "auto"

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
