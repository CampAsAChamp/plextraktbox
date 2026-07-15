"""In-memory source used by fakes and tests."""

from __future__ import annotations

from dataclasses import dataclass, field

from plextraktbox.sync.media_item import MediaItem, MediaType, format_episode_title
from plextraktbox.sync.plans import ApplyResult, ChangeAction, PlannedChange
from plextraktbox.sync.sources.base import NotSupported, Source, SourceCapabilities


def _clone_item(item: MediaItem, *, source: str) -> MediaItem:
    return MediaItem(
        title=item.title,
        media_type=item.media_type,
        identifiers=dict(item.identifiers),
        watchlisted=item.watchlisted,
        rating=item.rating,
        watched=item.watched,
        watched_at=item.watched_at,
        source=source,
        source_key=item.source_key or item.match_key() or item.title,
        season=item.season,
        episode=item.episode,
    )


@dataclass
class MemorySource(Source):
    """Mutable in-memory backing store for a service."""

    name: str
    capabilities: SourceCapabilities = field(default_factory=SourceCapabilities)
    watchlist: dict[str, MediaItem] = field(default_factory=dict)
    ratings: dict[str, MediaItem] = field(default_factory=dict)
    watched: dict[str, MediaItem] = field(default_factory=dict)

    def seed_watchlist(self, items: list[MediaItem]) -> None:
        for item in items:
            key = item.source_key or item.match_key() or item.title
            self.watchlist[key] = _clone_item(item, source=self.name)

    def seed_ratings(self, items: list[MediaItem]) -> None:
        for item in items:
            key = item.source_key or item.match_key() or item.title
            self.ratings[key] = _clone_item(item, source=self.name)

    def seed_watched(self, items: list[MediaItem]) -> None:
        for item in items:
            key = item.source_key or item.match_key() or item.title
            self.watched[key] = _clone_item(item, source=self.name)

    async def fetch_watchlist(self) -> list[MediaItem]:
        return list(self.watchlist.values())

    async def fetch_ratings(self) -> list[MediaItem]:
        return list(self.ratings.values())

    async def fetch_watched(self) -> list[MediaItem]:
        return list(self.watched.values())

    async def apply_watchlist(
        self,
        changes: list[PlannedChange],
        *,
        dry_run: bool,
    ) -> ApplyResult:
        if not self.capabilities.watchlist_write:
            raise NotSupported(f"{self.name} does not support watchlist writes")
        return await self._apply(changes, dry_run=dry_run, store=self.watchlist, field="watchlisted")

    async def apply_ratings(
        self,
        changes: list[PlannedChange],
        *,
        dry_run: bool,
    ) -> ApplyResult:
        if not self.capabilities.ratings_write:
            raise NotSupported(f"{self.name} does not support ratings writes")
        return await self._apply(changes, dry_run=dry_run, store=self.ratings, field="rating")

    async def apply_watched(
        self,
        changes: list[PlannedChange],
        *,
        dry_run: bool,
    ) -> ApplyResult:
        if not self.capabilities.watched_write:
            raise NotSupported(f"{self.name} does not support watched writes")
        return await self._apply(changes, dry_run=dry_run, store=self.watched, field="watched")

    async def _apply(
        self,
        changes: list[PlannedChange],
        *,
        dry_run: bool,
        store: dict[str, MediaItem],
        field: str,
    ) -> ApplyResult:
        result = ApplyResult()
        for change in changes:
            key = change.item.source_key or change.item.match_key() or change.item.title
            try:
                if change.action == ChangeAction.ADD:
                    if dry_run:
                        result.applied += 1
                        continue
                    item = _clone_item(change.item, source=self.name)
                    if field == "watchlisted":
                        item.watchlisted = True
                    elif field == "rating":
                        item.rating = change.new_value
                    elif field == "watched":
                        item.watched = True
                        item.watched_at = change.item.watched_at
                    store[key] = item
                    result.applied += 1
                elif change.action == ChangeAction.REMOVE:
                    if key not in store:
                        result.skipped += 1
                        continue
                    if dry_run:
                        result.applied += 1
                        continue
                    del store[key]
                    result.applied += 1
                elif change.action == ChangeAction.UPDATE:
                    existing = store.get(key)
                    if existing is None:
                        if dry_run:
                            result.applied += 1
                            continue
                        item = _clone_item(change.item, source=self.name)
                        setattr(item, field, change.new_value)
                        store[key] = item
                        result.applied += 1
                        continue
                    if dry_run:
                        result.applied += 1
                        continue
                    setattr(existing, field, change.new_value)
                    if field == "watched" and change.item.watched_at is not None:
                        existing.watched_at = change.item.watched_at
                    result.applied += 1
            except Exception:
                result.errors += 1
        return result


def movie(
    *,
    title: str,
    tmdb: str | None = None,
    imdb: str | None = None,
    tvdb: str | None = None,
    source: str = "",
    source_key: str = "",
    watchlisted: bool = False,
    rating: float | None = None,
    watched: bool = False,
) -> MediaItem:
    identifiers: dict[str, str] = {}
    if tmdb:
        identifiers["tmdb"] = tmdb
    if imdb:
        identifiers["imdb"] = imdb
    if tvdb:
        identifiers["tvdb"] = tvdb
    key = source_key or (f"tmdb:{tmdb}" if tmdb else title)
    return MediaItem(
        title=title,
        media_type=MediaType.MOVIE,
        identifiers=identifiers,
        watchlisted=watchlisted,
        rating=rating,
        watched=watched,
        source=source,
        source_key=key,
    )


def show(
    *,
    title: str,
    tmdb: str | None = None,
    imdb: str | None = None,
    tvdb: str | None = None,
    source: str = "",
    source_key: str = "",
    watchlisted: bool = False,
    rating: float | None = None,
    watched: bool = False,
) -> MediaItem:
    identifiers: dict[str, str] = {}
    if tmdb:
        identifiers["tmdb"] = tmdb
    if imdb:
        identifiers["imdb"] = imdb
    if tvdb:
        identifiers["tvdb"] = tvdb
    key = source_key or (f"tmdb:{tmdb}" if tmdb else title)
    return MediaItem(
        title=title,
        media_type=MediaType.SHOW,
        identifiers=identifiers,
        watchlisted=watchlisted,
        rating=rating,
        watched=watched,
        source=source,
        source_key=key,
    )


def episode(
    *,
    title: str,
    season: int,
    episode: int,
    tmdb: str | None = None,
    imdb: str | None = None,
    tvdb: str | None = None,
    source: str = "",
    source_key: str = "",
    watched: bool = False,
) -> MediaItem:
    identifiers: dict[str, str] = {}
    if tmdb:
        identifiers["tmdb"] = tmdb
    if imdb:
        identifiers["imdb"] = imdb
    if tvdb:
        identifiers["tvdb"] = tvdb
    display = format_episode_title(title, season, episode)
    key = source_key or (f"tmdb:{tmdb}:s{season}e{episode}" if tmdb else display)
    return MediaItem(
        title=display,
        media_type=MediaType.EPISODE,
        identifiers=identifiers,
        watched=watched,
        source=source,
        source_key=key,
        season=season,
        episode=episode,
    )
