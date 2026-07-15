"""Persisted Trakt list snapshots with TTL (Phase 21)."""

from __future__ import annotations

from datetime import datetime

from sqlmodel import Field, SQLModel


class TraktListCache(SQLModel, table=True):
    __tablename__ = "trakt_list_cache"

    list_kind: str = Field(primary_key=True, max_length=32)
    account_key: str = Field(primary_key=True, max_length=128)
    items_json: str = Field(default="[]")
    fetched_at: datetime = Field()
