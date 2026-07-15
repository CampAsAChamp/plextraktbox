"""Persisted external id → Plex Discover metadata key map (Phase 21)."""

from __future__ import annotations

from datetime import datetime

from sqlmodel import Field, SQLModel


class PlexDiscoverKeyCache(SQLModel, table=True):
    __tablename__ = "plex_discover_key_cache"

    id_provider: str = Field(primary_key=True, max_length=16)
    external_id: str = Field(primary_key=True, max_length=64)
    libtype: str = Field(primary_key=True, max_length=16, default="movie")
    discover_key: str = Field(max_length=128)
    updated_at: datetime = Field()
