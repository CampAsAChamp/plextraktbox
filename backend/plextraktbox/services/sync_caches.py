"""Clear / report sync fetch & resolve caches (Phase 21)."""

from __future__ import annotations

from dataclasses import dataclass

from sqlmodel import Session

from plextraktbox.services import (
    letterboxd_export_cache,
    letterboxd_slug_cache,
    plex_discover_key_cache,
    trakt_list_cache,
)


@dataclass(frozen=True)
class ClearSyncCachesResult:
    letterboxd_export: int
    letterboxd_slug: int
    trakt_lists: int
    discover_keys: int


def clear_sync_caches(
    session: Session,
    *,
    letterboxd_export: bool = True,
    letterboxd_slug: bool = True,
    trakt_lists: bool = True,
    discover_keys: bool = True,
) -> ClearSyncCachesResult:
    export_count = 0
    slug_count = 0
    trakt_count = 0
    discover_count = 0

    if letterboxd_export:
        export_count = letterboxd_export_cache.clear_all_export_caches()
    if letterboxd_slug:
        slug_count = letterboxd_slug_cache.clear_slug_cache(session)
    if trakt_lists:
        trakt_count = trakt_list_cache.clear_trakt_list_cache(session)
    if discover_keys:
        discover_count = plex_discover_key_cache.clear_discover_key_cache(session)

    return ClearSyncCachesResult(
        letterboxd_export=export_count,
        letterboxd_slug=slug_count,
        trakt_lists=trakt_count,
        discover_keys=discover_count,
    )
