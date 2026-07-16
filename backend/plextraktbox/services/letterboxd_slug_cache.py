"""Letterboxd slug → TMDB/IMDb resolve cache (Phase 21)."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime, timedelta

from sqlmodel import Session, select

from plextraktbox.logging_setup import get_logger
from plextraktbox.models.letterboxd_slug_cache import LetterboxdSlugCache

log = get_logger(__name__)

DEFAULT_MISS_TTL_HOURS = 1

Resolver = Callable[[str, str, str | None], dict[str, str] | None]


def _engine():
    from plextraktbox import db

    return db.engine


def clear_slug_cache(session: Session | None = None) -> int:
    owns = session is None
    if owns:
        session = Session(_engine())
    assert session is not None
    try:
        rows = list(session.exec(select(LetterboxdSlugCache)).all())
        count = len(rows)
        for row in rows:
            session.delete(row)
        session.commit()
        return count
    finally:
        if owns:
            session.close()


def lookup_slug(session: Session, slug: str) -> LetterboxdSlugCache | None:
    return session.get(LetterboxdSlugCache, slug)


def write_hit(
    session: Session,
    *,
    slug: str,
    identifiers: dict[str, str],
    title: str,
    year: str | None,
) -> None:
    now = datetime.now(UTC)
    row = session.get(LetterboxdSlugCache, slug)
    if row is None:
        row = LetterboxdSlugCache(slug=slug)
        session.add(row)
    row.tmdb = identifiers.get("tmdb")
    row.imdb = identifiers.get("imdb")
    row.title = title
    row.year = year
    row.resolved_at = now
    row.miss_until = None
    session.commit()


def write_miss(
    session: Session,
    *,
    slug: str,
    title: str,
    year: str | None,
    miss_ttl_hours: int = DEFAULT_MISS_TTL_HOURS,
) -> None:
    now = datetime.now(UTC)
    row = session.get(LetterboxdSlugCache, slug)
    if row is None:
        row = LetterboxdSlugCache(slug=slug)
        session.add(row)
    row.title = title
    row.year = year
    row.tmdb = None
    row.imdb = None
    row.resolved_at = None
    row.miss_until = now + timedelta(hours=miss_ttl_hours)
    session.commit()


def cached_identifiers(row: LetterboxdSlugCache) -> dict[str, str] | None:
    """Return identifiers for a successful hit, None if this is a miss or empty."""
    if row.miss_until is not None:
        return None
    ids: dict[str, str] = {}
    if row.tmdb:
        ids["tmdb"] = row.tmdb
    if row.imdb:
        ids["imdb"] = row.imdb
    return ids or None


def is_negative_cache_active(row: LetterboxdSlugCache) -> bool:
    if row.miss_until is None:
        return False
    miss_until = row.miss_until
    if miss_until.tzinfo is None:
        miss_until = miss_until.replace(tzinfo=UTC)
    return datetime.now(UTC) < miss_until


def wrap_resolver(
    resolver: Resolver,
    *,
    miss_ttl_hours: int = DEFAULT_MISS_TTL_HOURS,
) -> Resolver:
    """Return a resolver that reads/writes the slug cache around ``resolver``."""
    hits = 0
    misses = 0
    newly_resolved = 0

    def resolve(slug: str, title: str, year: str | None = None) -> dict[str, str] | None:
        nonlocal hits, misses, newly_resolved
        with Session(_engine()) as session:
            row = lookup_slug(session, slug)
            if row is not None:
                if is_negative_cache_active(row):
                    hits += 1
                    log.debug(
                        "sync.cache.letterboxd_slug.hit",
                        message=f'Letterboxd slug cache negative hit for "{title}"',
                        slug=slug,
                        negative=True,
                    )
                    return None
                ids = cached_identifiers(row)
                if ids is not None:
                    hits += 1
                    log.debug(
                        "sync.cache.letterboxd_slug.hit",
                        message=f'Letterboxd slug cache hit for "{title}"',
                        slug=slug,
                        identifiers=ids,
                    )
                    return ids

            misses += 1
            result = resolver(slug, title, year)
            if result:
                newly_resolved += 1
                write_hit(session, slug=slug, identifiers=result, title=title, year=year)
            else:
                write_miss(
                    session,
                    slug=slug,
                    title=title,
                    year=year,
                    miss_ttl_hours=miss_ttl_hours,
                )
            return result

    resolve.stats = lambda: {  # type: ignore[attr-defined]
        "hits": hits,
        "misses": misses,
        "newly_resolved": newly_resolved,
    }
    return resolve
