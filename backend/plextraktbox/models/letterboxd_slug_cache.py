"""Persisted Letterboxd slug → external identifier map (Phase 21)."""

from __future__ import annotations

from datetime import datetime

from sqlmodel import Field, SQLModel


class LetterboxdSlugCache(SQLModel, table=True):
    __tablename__ = "letterboxd_slug_cache"

    slug: str = Field(primary_key=True, max_length=256)
    tmdb: str | None = Field(default=None, max_length=64)
    imdb: str | None = Field(default=None, max_length=64)
    title: str | None = Field(default=None, max_length=512)
    year: str | None = Field(default=None, max_length=16)
    resolved_at: datetime | None = Field(default=None)
    miss_until: datetime | None = Field(default=None)
