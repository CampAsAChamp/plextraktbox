"""Third-party service connections (Plex, Trakt, Letterboxd, TMDB)."""

from __future__ import annotations

import json
from datetime import datetime
from enum import StrEnum
from typing import Any

from sqlmodel import Field, SQLModel


class Service(StrEnum):
    PLEX = "plex"
    TRAKT = "trakt"
    LETTERBOXD = "letterboxd"
    TMDB = "tmdb"


class ConnectionStatus(StrEnum):
    OK = "ok"
    UNCONFIGURED = "unconfigured"
    NEEDS_REAUTH = "needs_reauth"
    ERROR = "error"


class Connection(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    service: Service = Field(unique=True, index=True)
    status: ConnectionStatus = Field(default=ConnectionStatus.UNCONFIGURED)
    config_json: str = Field(default="{}")
    secret_enc: str = Field(default="")
    token_expires_at: datetime | None = Field(default=None, nullable=True)

    def public_config(self) -> dict[str, Any]:
        try:
            data = json.loads(self.config_json)
        except json.JSONDecodeError:
            return {}
        return data if isinstance(data, dict) else {}
