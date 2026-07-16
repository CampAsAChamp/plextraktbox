"""Shared helpers for client-backed source apply paths."""

from __future__ import annotations

import asyncio
import threading
from collections.abc import Callable

from plextraktbox.logging_setup import get_logger
from plextraktbox.sync.cancellation import check_cancelled
from plextraktbox.sync.plans import ApplyResult, PlannedChange

log = get_logger("sync.apply")


async def apply_live(
    changes: list[PlannedChange],
    *,
    dry_run: bool,
    apply_batch: Callable[[list[PlannedChange]], None],
    apply_one: Callable[[PlannedChange], None] | None = None,
    cancel_event: threading.Event | None = None,
) -> ApplyResult:
    """Apply planned changes with dry-run support and per-item fault isolation."""
    result = ApplyResult()
    if not changes:
        return result
    if dry_run:
        result.applied = len(changes)
        return result

    check_cancelled(cancel_event)
    single = apply_one or (lambda change: apply_batch([change]))
    try:
        await asyncio.to_thread(apply_batch, changes)
        result.applied = len(changes)
        return result
    except Exception as exc:
        log.warning(
            "sync.apply.batch_failed",
            message="Batch apply failed; retrying one item at a time",
            error=str(exc),
            count=len(changes),
        )

    for change in changes:
        check_cancelled(cancel_event)
        try:
            await asyncio.to_thread(single, change)
            result.applied += 1
        except Exception as exc:
            result.errors += 1
            log.warning(
                "sync.apply.item_failed",
                message=f'Failed to apply "{change.item.title}": {exc}',
                title=change.item.title,
                target=change.target_source,
                data_type=change.data_type.value,
                error=str(exc),
            )
    return result
