"""Sync execution context: sources, cache, logging, dry-run flag."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import structlog

from plextraktbox.sync.plans import DataType

if TYPE_CHECKING:
    from plextraktbox.sync.sources.base import Source


@dataclass
class SyncContext:
    sources: dict[str, Source]
    data_types: set[DataType]
    dry_run: bool
    log: structlog.stdlib.BoundLogger = field(default_factory=lambda: structlog.get_logger("sync"))
    _cache: dict[tuple[str, DataType], list] = field(default_factory=dict, repr=False)

    async def fetch(self, source_name: str, data_type: DataType) -> list:
        from plextraktbox.sync.media_item import MediaItem

        cache_key = (source_name, data_type)
        if cache_key in self._cache:
            return self._cache[cache_key]

        source = self.sources.get(source_name)
        if source is None:
            raise KeyError(f"Unknown source: {source_name}")

        if data_type == DataType.WATCHLIST:
            items = await source.fetch_watchlist()
        elif data_type == DataType.RATINGS:
            items = await source.fetch_ratings()
        elif data_type == DataType.WATCHED:
            items = await source.fetch_watched()
        else:
            raise ValueError(f"Unsupported data type: {data_type}")

        if not isinstance(items, list):
            raise TypeError(f"{source_name}.{data_type} must return a list")
        for item in items:
            if not isinstance(item, MediaItem):
                raise TypeError(f"{source_name}.{data_type} returned non-MediaItem")

        self._cache[cache_key] = items
        return items

    def source_names(self) -> list[str]:
        return list(self.sources.keys())
