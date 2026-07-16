"""TTL cache for Trakt watchlist / ratings / watched list fetches (Phase 21)."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlmodel import Session

from plextraktbox.logging_setup import get_logger
from plextraktbox.models.trakt_list_cache import TraktListCache
from plextraktbox.services.cache_helpers import clear_all_rows, get_engine, is_within_ttl
from plextraktbox.sync.media_item import MediaItem, MediaType

log = get_logger(__name__)

LIST_WATCHLIST = "watchlist"
LIST_RATINGS = "ratings"
LIST_WATCHED = "watched"


def account_key_for_token(access_token: str) -> str:
    return hashlib.sha256(access_token.encode("utf-8")).hexdigest()[:32]


def _serialize_items(items: list[MediaItem]) -> str:
    payload: list[dict[str, Any]] = []
    for item in items:
        payload.append(
            {
                "title": item.title,
                "media_type": item.media_type.value,
                "identifiers": dict(item.identifiers),
                "watchlisted": item.watchlisted,
                "rating": item.rating,
                "watched": item.watched,
                "watched_at": item.watched_at.isoformat() if item.watched_at else None,
                "source": item.source,
                "source_key": item.source_key,
                "season": item.season,
                "episode": item.episode,
            }
        )
    return json.dumps(payload)


def _deserialize_items(raw: str) -> list[MediaItem]:
    data = json.loads(raw)
    if not isinstance(data, list):
        return []
    items: list[MediaItem] = []
    for row in data:
        if not isinstance(row, dict):
            continue
        watched_at = None
        raw_watched = row.get("watched_at")
        if isinstance(raw_watched, str) and raw_watched:
            try:
                watched_at = datetime.fromisoformat(raw_watched)
            except ValueError:
                watched_at = None
        try:
            media_type = MediaType(str(row.get("media_type", "movie")))
        except ValueError:
            continue
        identifiers = row.get("identifiers")
        if not isinstance(identifiers, dict):
            identifiers = {}
        items.append(
            MediaItem(
                title=str(row.get("title", "")),
                media_type=media_type,
                identifiers={str(k): str(v) for k, v in identifiers.items()},
                watchlisted=bool(row.get("watchlisted", False)),
                rating=row.get("rating") if isinstance(row.get("rating"), (int, float)) else None,
                watched=bool(row.get("watched", False)),
                watched_at=watched_at,
                source=str(row.get("source", "")),
                source_key=str(row.get("source_key", "")),
                season=row.get("season") if isinstance(row.get("season"), int) else None,
                episode=row.get("episode") if isinstance(row.get("episode"), int) else None,
            )
        )
    return items


def clear_trakt_list_cache(session: Session | None = None) -> int:
    return clear_all_rows(TraktListCache, session)


def invalidate_list(list_kind: str, access_token: str) -> None:
    key = account_key_for_token(access_token)
    with Session(get_engine()) as session:
        row = session.get(TraktListCache, (list_kind, key))
        if row is not None:
            session.delete(row)
            session.commit()
            log.info(
                "sync.cache.trakt_list.invalidated",
                message=f"Invalidated Trakt {list_kind} cache",
                list_kind=list_kind,
            )


def invalidate_for_apply(list_kinds: list[str], access_token: str) -> None:
    for kind in list_kinds:
        invalidate_list(kind, access_token)


def get_cached_list(
    list_kind: str,
    access_token: str,
    *,
    ttl_minutes: int,
) -> list[MediaItem] | None:
    key = account_key_for_token(access_token)
    with Session(get_engine()) as session:
        row = session.get(TraktListCache, (list_kind, key))
        if row is None:
            return None
        if not is_within_ttl(row.fetched_at, ttl=timedelta(minutes=ttl_minutes)):
            return None
        return _deserialize_items(row.items_json)


def store_list(list_kind: str, access_token: str, items: list[MediaItem]) -> None:
    key = account_key_for_token(access_token)
    with Session(get_engine()) as session:
        row = session.get(TraktListCache, (list_kind, key))
        if row is None:
            row = TraktListCache(
                list_kind=list_kind,
                account_key=key,
                items_json="[]",
                fetched_at=datetime.now(UTC),
            )
            session.add(row)
        row.items_json = _serialize_items(items)
        row.fetched_at = datetime.now(UTC)
        session.commit()


def get_or_fetch_list(
    list_kind: str,
    access_token: str,
    *,
    ttl_minutes: int,
    force: bool,
    fetch: Callable[[], list[MediaItem]],
) -> list[MediaItem]:
    if not force:
        cached = get_cached_list(list_kind, access_token, ttl_minutes=ttl_minutes)
        if cached is not None:
            log.info(
                "sync.cache.trakt_list.hit",
                message=f"Trakt {list_kind} cache hit ({len(cached)} item(s))",
                list_kind=list_kind,
                count=len(cached),
            )
            return cached

    status = "forced" if force else "miss"
    log.info(
        f"sync.cache.trakt_list.{status}",
        message=f"Fetching Trakt {list_kind} ({'force refresh' if force else 'cache miss or expired'})",
        list_kind=list_kind,
    )
    items = fetch()
    store_list(list_kind, access_token, items)
    return items
