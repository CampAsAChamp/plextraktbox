"""Sync engine orchestration."""

from __future__ import annotations

from collections import defaultdict

import structlog

from plextraktbox.sync.context import SyncContext
from plextraktbox.sync.plans import (
    ApplyResult,
    ChangeAction,
    DataType,
    PlannedChange,
    RunSummary,
)
from plextraktbox.sync.plugins import get_plugin_manager
from plextraktbox.sync.reconcilers import DEFAULT_RECONCILERS
from plextraktbox.sync.reconcilers.base import Reconciler


async def run_sync(ctx: SyncContext, reconcilers: list[Reconciler] | None = None) -> RunSummary:
    """Fetch → plan → log → apply for each enabled data type."""
    pm = get_plugin_manager()
    summary = RunSummary()
    log = ctx.log or structlog.get_logger("sync")
    active = reconcilers or DEFAULT_RECONCILERS
    active_by_type = {reconciler.data_type: reconciler for reconciler in active}

    pm.hook.before_run(ctx=ctx)

    for data_type in (DataType.WATCHLIST, DataType.RATINGS, DataType.WATCHED):
        if data_type not in ctx.data_types:
            continue
        reconciler = active_by_type.get(data_type)
        if reconciler is None:
            log.warning("sync.reconciler.missing", data_type=data_type.value)
            continue

        plan = await reconciler.plan(ctx)
        summary.planned += len(plan.changes)
        summary.matched += _count_matched(plan.changes)

        for change in plan.changes:
            prefix = "would" if ctx.dry_run else "will"
            log.info(
                "sync.plan",
                data_type=data_type.value,
                action=change.action.value,
                target=change.target_source,
                title=change.item.title,
                message=f"{prefix} {change.message}",
                dry_run=ctx.dry_run,
            )

        if not plan.changes:
            continue

        grouped = _group_by_target_and_action(plan.changes)
        for (target_name, action), changes in grouped.items():
            source = ctx.sources.get(target_name)
            if source is None:
                summary.errors += len(changes)
                continue

            try:
                result = await _apply_changes(source, data_type, changes, dry_run=ctx.dry_run)
            except Exception as exc:
                log.warning(
                    "sync.apply.failed",
                    target=target_name,
                    data_type=data_type.value,
                    error=str(exc),
                )
                summary.errors += len(changes)
                pm.hook.after_item(
                    ctx=ctx,
                    data_type=data_type.value,
                    message=str(exc),
                    error=exc,
                )
                continue

            _merge_summary(summary, data_type, action, result)

            for change in changes:
                pm.hook.after_item(
                    ctx=ctx,
                    data_type=data_type.value,
                    message=change.message,
                )

    pm.hook.after_run(ctx=ctx, summary=summary)
    return summary


def _group_by_target_and_action(
    changes: list[PlannedChange],
) -> dict[tuple[str, ChangeAction], list[PlannedChange]]:
    grouped: dict[tuple[str, ChangeAction], list[PlannedChange]] = defaultdict(list)
    for change in changes:
        grouped[(change.target_source, change.action)].append(change)
    return grouped


async def _apply_changes(
    source: object,
    data_type: DataType,
    changes: list[PlannedChange],
    *,
    dry_run: bool,
) -> ApplyResult:
    if data_type == DataType.WATCHLIST:
        return await source.apply_watchlist(changes, dry_run=dry_run)  # type: ignore[attr-defined]
    if data_type == DataType.RATINGS:
        return await source.apply_ratings(changes, dry_run=dry_run)  # type: ignore[attr-defined]
    return await source.apply_watched(changes, dry_run=dry_run)  # type: ignore[attr-defined]


def _count_matched(changes: list[PlannedChange]) -> int:
    return sum(1 for change in changes if change.action == ChangeAction.UPDATE)


def _merge_summary(
    summary: RunSummary,
    data_type: DataType,
    action: ChangeAction,
    result: ApplyResult,
) -> None:
    if action == ChangeAction.ADD:
        summary.added += result.applied
    elif action == ChangeAction.REMOVE:
        summary.removed += result.applied
    elif action == ChangeAction.UPDATE:
        if data_type == DataType.RATINGS:
            summary.rated += result.applied
        elif data_type == DataType.WATCHED:
            summary.watched += result.applied
    summary.skipped += result.skipped
    summary.errors += result.errors
