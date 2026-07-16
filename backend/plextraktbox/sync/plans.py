"""Sync plans, planned changes, and run summaries."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from plextraktbox.sync.media_item import MediaItem


class DataType(StrEnum):
    WATCHLIST = "watchlist"
    RATINGS = "ratings"
    WATCHED = "watched"


class ChangeAction(StrEnum):
    ADD = "add"
    REMOVE = "remove"
    UPDATE = "update"


@dataclass
class PlannedChange:
    action: ChangeAction
    data_type: DataType
    target_source: str
    item: MediaItem
    field: str
    old_value: Any
    new_value: Any
    message: str


@dataclass
class ApplyResult:
    applied: int = 0
    skipped: int = 0
    errors: int = 0


@dataclass
class UnmatchedItem:
    source: str
    data_type: str
    title: str
    source_key: str
    reason: str
    identifiers: dict[str, str] = field(default_factory=dict)


@dataclass
class RunSummary:
    matched: int = 0
    added: int = 0
    removed: int = 0
    rated: int = 0
    watched: int = 0
    skipped: int = 0
    errors: int = 0
    planned: int = 0
    shows_added: int = 0
    shows_removed: int = 0
    episodes_watched: int = 0
    unmatched: list[UnmatchedItem] = field(default_factory=list)

    def merge_apply(
        self,
        result: ApplyResult,
        *,
        data_type: DataType,
        action: ChangeAction,
        changes: list[PlannedChange],
    ) -> None:
        """Fold an apply batch into summary counters (including TV breakdown)."""
        from plextraktbox.sync.media_item import MediaType

        if action == ChangeAction.ADD:
            self.added += result.applied
        elif action == ChangeAction.REMOVE:
            self.removed += result.applied
        elif action == ChangeAction.UPDATE:
            if data_type == DataType.RATINGS:
                self.rated += result.applied
            elif data_type == DataType.WATCHED:
                self.watched += result.applied
        self.skipped += result.skipped
        self.errors += result.errors

        # TV breakdown — only when the whole batch applied (incl. dry-run).
        if result.applied == len(changes) and changes:
            if data_type == DataType.WATCHLIST and action == ChangeAction.ADD:
                self.shows_added += sum(1 for change in changes if change.item.media_type == MediaType.SHOW)
            elif data_type == DataType.WATCHLIST and action == ChangeAction.REMOVE:
                self.shows_removed += sum(1 for change in changes if change.item.media_type == MediaType.SHOW)
            elif data_type == DataType.WATCHED and action == ChangeAction.UPDATE:
                self.episodes_watched += sum(
                    1 for change in changes if change.item.media_type == MediaType.EPISODE
                )

    def to_dict(self) -> dict[str, Any]:
        return {
            "matched": self.matched,
            "added": self.added,
            "removed": self.removed,
            "rated": self.rated,
            "watched": self.watched,
            "skipped": self.skipped,
            "errors": self.errors,
            "planned": self.planned,
            "shows_added": self.shows_added,
            "shows_removed": self.shows_removed,
            "episodes_watched": self.episodes_watched,
            "unmatched_count": len(self.unmatched),
            "unmatched": [
                {
                    "source": item.source,
                    "data_type": item.data_type,
                    "title": item.title,
                    "source_key": item.source_key,
                    "reason": item.reason,
                    "identifiers": dict(item.identifiers),
                }
                for item in self.unmatched
            ],
        }


@dataclass
class ReconcilePlan:
    data_type: DataType
    changes: list[PlannedChange] = field(default_factory=list)
