"""Stateless cross-service media matching by identifier priority."""

from __future__ import annotations

from plextraktbox.sync.media_item import IDENTIFIER_PRIORITY, MediaItem


class MediaMatcher:
    """Index items by TMDB → IMDb → TVDB and resolve cross-service matches."""

    def __init__(self) -> None:
        self._index: dict[str, dict[str, MediaItem]] = {key: {} for key in IDENTIFIER_PRIORITY}

    def add(self, item: MediaItem) -> None:
        for key in IDENTIFIER_PRIORITY:
            if value := item.identifiers.get(key):
                self._index[key].setdefault(value, item)

    def add_many(self, items: list[MediaItem]) -> None:
        for item in items:
            self.add(item)

    def find(self, item: MediaItem) -> MediaItem | None:
        for key in IDENTIFIER_PRIORITY:
            if (value := item.identifiers.get(key)) and (match := self._index[key].get(value)):
                return match
        return None

    def match_pairs(
        self,
        left: list[MediaItem],
        right: list[MediaItem],
    ) -> list[tuple[MediaItem, MediaItem]]:
        right_index = MediaMatcher()
        right_index.add_many(right)
        pairs: list[tuple[MediaItem, MediaItem]] = []
        seen: set[str] = set()
        for left_item in left:
            right_item = right_index.find(left_item)
            if right_item is None:
                continue
            key = left_item.match_key() or left_item.source_key
            if key in seen:
                continue
            seen.add(key)
            pairs.append((left_item, right_item))
        return pairs

    def unmatched_in_truth(
        self,
        truth_items: list[MediaItem],
        other_items: list[MediaItem],
    ) -> list[MediaItem]:
        other = MediaMatcher()
        other.add_many(other_items)
        return [item for item in truth_items if other.find(item) is None]

    def unmatched_in_other(
        self,
        truth_items: list[MediaItem],
        other_items: list[MediaItem],
    ) -> list[MediaItem]:
        truth = MediaMatcher()
        truth.add_many(truth_items)
        return [item for item in other_items if truth.find(item) is None]
