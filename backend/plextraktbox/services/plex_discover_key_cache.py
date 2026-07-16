"""Persisted external id → Plex Discover metadata key (Phase 21)."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlmodel import Session

from plextraktbox.logging_setup import get_logger
from plextraktbox.models.plex_discover_key_cache import PlexDiscoverKeyCache
from plextraktbox.services.cache_helpers import clear_all_rows, get_engine
from plextraktbox.sync.media_item import MediaItem, MediaType

log = get_logger(__name__)


def _libtype_for(item: MediaItem) -> str:
    return "show" if item.media_type == MediaType.SHOW else "movie"


def _cache_keys(item: MediaItem) -> list[tuple[str, str]]:
    keys: list[tuple[str, str]] = []
    for provider in ("tmdb", "imdb", "tvdb"):
        value = item.identifiers.get(provider)
        if value:
            keys.append((provider, value))
    return keys


def clear_discover_key_cache(session: Session | None = None) -> int:
    return clear_all_rows(PlexDiscoverKeyCache, session)


def lookup_discover_key(item: MediaItem) -> str | None:
    libtype = _libtype_for(item)
    with Session(get_engine()) as session:
        for provider, external_id in _cache_keys(item):
            row = session.get(PlexDiscoverKeyCache, (provider, external_id, libtype))
            if row is not None and row.discover_key:
                log.debug(
                    "sync.cache.discover_key.hit",
                    message=f'Discover key cache hit for "{item.title}"',
                    title=item.title,
                    provider=provider,
                    external_id=external_id,
                )
                return row.discover_key
    return None


def store_discover_key(item: MediaItem, discover_key: str) -> None:
    libtype = _libtype_for(item)
    now = datetime.now(UTC)
    with Session(get_engine()) as session:
        for provider, external_id in _cache_keys(item):
            row = session.get(PlexDiscoverKeyCache, (provider, external_id, libtype))
            if row is None:
                row = PlexDiscoverKeyCache(
                    id_provider=provider,
                    external_id=external_id,
                    libtype=libtype,
                    discover_key=discover_key,
                    updated_at=now,
                )
                session.add(row)
            else:
                row.discover_key = discover_key
                row.updated_at = now
        session.commit()
    log.debug(
        "sync.cache.discover_key.store",
        message=f'Stored Discover key for "{item.title}"',
        title=item.title,
        discover_key=discover_key,
    )


def invalidate_discover_key(item: MediaItem) -> None:
    libtype = _libtype_for(item)
    with Session(get_engine()) as session:
        for provider, external_id in _cache_keys(item):
            row = session.get(PlexDiscoverKeyCache, (provider, external_id, libtype))
            if row is not None:
                session.delete(row)
        session.commit()
