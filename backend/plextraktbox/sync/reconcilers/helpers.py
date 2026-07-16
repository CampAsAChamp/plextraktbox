"""Shared helpers for reconciler planning loops."""

from __future__ import annotations

from collections.abc import Iterator

from plextraktbox.sync.context import SyncContext
from plextraktbox.sync.matcher import MediaMatcher
from plextraktbox.sync.media_item import MediaItem
from plextraktbox.sync.sources.base import Source


def iter_writable_targets(
    ctx: SyncContext,
    target_names: tuple[str, ...],
    *,
    write_capability: str,
) -> Iterator[tuple[str, Source]]:
    """Yield ``(name, source)`` for targets present in ``ctx`` with write capability."""
    for target_name in target_names:
        if target_name not in ctx.sources:
            continue
        target = ctx.sources[target_name]
        if not getattr(target.capabilities, write_capability, False):
            continue
        yield target_name, target


def build_matcher(items: list[MediaItem]) -> MediaMatcher:
    """Index ``items`` for identifier matching."""
    matcher = MediaMatcher()
    matcher.add_many(items)
    return matcher
