"""Exclude/ignore list helpers for sync media items."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from plextraktbox.sync.media_item import MediaItem

EXCLUDE_ID_KEYS = ("tmdb", "imdb", "tvdb")


def normalize_exclude_ids(raw: object) -> dict[str, set[str]]:
    """Parse exclude-id JSON into provider → id sets."""
    result: dict[str, set[str]] = {key: set() for key in EXCLUDE_ID_KEYS}
    if not isinstance(raw, dict):
        return result
    for key in EXCLUDE_ID_KEYS:
        values = raw.get(key)
        if not isinstance(values, list):
            continue
        for item in values:
            text = str(item).strip()
            if text:
                result[key].add(text)
    return result


def dump_exclude_ids(exclude_ids: dict[str, set[str]] | dict[str, list[str]]) -> dict[str, list[str]]:
    """Serialize exclude ids with sorted lists for stable JSON."""
    out: dict[str, list[str]] = {}
    for key in EXCLUDE_ID_KEYS:
        values = exclude_ids.get(key, [])
        if isinstance(values, set):
            cleaned = sorted(v.strip() for v in values if v and str(v).strip())
        else:
            cleaned = sorted(str(v).strip() for v in values if str(v).strip())
        if cleaned:
            out[key] = cleaned
    return out


def merge_exclude_ids(*sets: dict[str, set[str]]) -> dict[str, set[str]]:
    merged: dict[str, set[str]] = {key: set() for key in EXCLUDE_ID_KEYS}
    for exclude_set in sets:
        for key in EXCLUDE_ID_KEYS:
            merged[key].update(exclude_set.get(key, set()))
    return merged


def item_excluded(item: MediaItem, exclude_ids: dict[str, set[str]]) -> bool:
    """True when any of the item's TMDB/IMDb/TVDB ids is on the exclude list."""
    for key in EXCLUDE_ID_KEYS:
        value = item.identifiers.get(key)
        if value and value in exclude_ids.get(key, set()):
            return True
    return False


def filter_excluded_items(
    items: list[MediaItem],
    exclude_ids: dict[str, set[str]],
) -> tuple[list[MediaItem], int]:
    """Return (kept items, excluded count)."""
    if not any(exclude_ids.values()):
        return items, 0
    kept: list[MediaItem] = []
    excluded = 0
    for item in items:
        if item_excluded(item, exclude_ids):
            excluded += 1
        else:
            kept.append(item)
    return kept, excluded
