"""Shared sync test helpers."""

from __future__ import annotations

import structlog

from plextraktbox.sync.context import SyncContext
from plextraktbox.sync.plans import DataType
from plextraktbox.sync.sources.base import Source


def make_context(
    *,
    sources: dict[str, Source],
    data_types: set[DataType],
    dry_run: bool = False,
) -> SyncContext:
    return SyncContext(
        sources=sources,
        data_types=data_types,
        dry_run=dry_run,
        log=structlog.get_logger("test.sync"),
    )
