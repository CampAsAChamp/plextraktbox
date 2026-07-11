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
class RunSummary:
    matched: int = 0
    added: int = 0
    removed: int = 0
    rated: int = 0
    watched: int = 0
    skipped: int = 0
    errors: int = 0
    planned: int = 0

    def merge_apply(self, result: ApplyResult, *, action: ChangeAction) -> None:
        if action == ChangeAction.ADD:
            self.added += result.applied
        elif action == ChangeAction.REMOVE:
            self.removed += result.applied
        elif action == ChangeAction.UPDATE:
            pass
        self.skipped += result.skipped
        self.errors += result.errors

    def to_dict(self) -> dict[str, int]:
        return {
            "matched": self.matched,
            "added": self.added,
            "removed": self.removed,
            "rated": self.rated,
            "watched": self.watched,
            "skipped": self.skipped,
            "errors": self.errors,
            "planned": self.planned,
        }


@dataclass
class ReconcilePlan:
    data_type: DataType
    changes: list[PlannedChange] = field(default_factory=list)
