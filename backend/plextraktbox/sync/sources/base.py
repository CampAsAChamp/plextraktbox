"""Source adapter ABC and shared types."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from plextraktbox.sync.media_item import MediaItem
    from plextraktbox.sync.plans import ApplyResult, PlannedChange


class NotSupported(Exception):
    """Raised when a read-only source receives a write request."""


@dataclass(frozen=True)
class SourceCapabilities:
    watchlist_read: bool = True
    watchlist_write: bool = True
    ratings_read: bool = True
    ratings_write: bool = True
    watched_read: bool = True
    watched_write: bool = True


class Source(ABC):
    name: str
    capabilities: SourceCapabilities = SourceCapabilities()

    @abstractmethod
    async def fetch_watchlist(self) -> list[MediaItem]:
        raise NotImplementedError

    @abstractmethod
    async def fetch_ratings(self) -> list[MediaItem]:
        raise NotImplementedError

    @abstractmethod
    async def fetch_watched(self) -> list[MediaItem]:
        raise NotImplementedError

    @abstractmethod
    async def apply_watchlist(
        self,
        changes: list[PlannedChange],
        *,
        dry_run: bool,
    ) -> ApplyResult:
        raise NotImplementedError

    @abstractmethod
    async def apply_ratings(
        self,
        changes: list[PlannedChange],
        *,
        dry_run: bool,
    ) -> ApplyResult:
        raise NotImplementedError

    @abstractmethod
    async def apply_watched(
        self,
        changes: list[PlannedChange],
        *,
        dry_run: bool,
    ) -> ApplyResult:
        raise NotImplementedError
