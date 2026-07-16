"""Sync execution context: sources, cache, logging, dry-run flag."""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import structlog

from plextraktbox.sync.cancellation import check_cancelled
from plextraktbox.sync.excludes import EXCLUDE_ID_KEYS, filter_excluded_items
from plextraktbox.sync.plans import DataType

if TYPE_CHECKING:
    from plextraktbox.sync.sources.base import Source


@dataclass
class SyncContext:
    sources: dict[str, Source]
    data_types: set[DataType]
    dry_run: bool
    log: structlog.stdlib.BoundLogger = field(default_factory=lambda: structlog.get_logger("sync"))
    exclude_ids: dict[str, set[str]] = field(default_factory=lambda: {key: set() for key in EXCLUDE_ID_KEYS})
    cancel_event: threading.Event | None = None
    _cache: dict[tuple[str, DataType], list] = field(default_factory=dict, repr=False)

    def raise_if_cancelled(self) -> None:
        check_cancelled(self.cancel_event)

    async def fetch(self, source_name: str, data_type: DataType) -> list:
        from plextraktbox.sync.media_item import MediaItem

        self.raise_if_cancelled()

        cache_key = (source_name, data_type)
        if cache_key in self._cache:
            return self._cache[cache_key]

        source = self.sources.get(source_name)
        if source is None:
            raise KeyError(f"Unknown source: {source_name}")

        self.log.info(
            "sync.fetch.start",
            message=f"Fetching {data_type.value} from {source_name}",
            source=source_name,
            data_type=data_type.value,
        )

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

        items, excluded = filter_excluded_items(items, self.exclude_ids)
        with_ids = sum(1 for item in items if item.identifiers)
        self.log.info(
            "sync.fetch.done",
            message=(
                f"Fetched {len(items)} {data_type.value} item(s) from {source_name} "
                f"({with_ids} with IDs" + (f", {excluded} excluded" if excluded else "") + ")"
            ),
            source=source_name,
            data_type=data_type.value,
            count=len(items),
            with_ids=with_ids,
            excluded=excluded,
        )

        self._cache[cache_key] = items
        return items

    def source_names(self) -> list[str]:
        return list(self.sources.keys())
