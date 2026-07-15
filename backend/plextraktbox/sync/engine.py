"""Sync engine orchestration."""

from __future__ import annotations

from collections import defaultdict

import structlog

from plextraktbox.sync.context import SyncContext
from plextraktbox.sync.matcher import MediaMatcher
from plextraktbox.sync.plans import (
    ApplyResult,
    ChangeAction,
    DataType,
    PlannedChange,
    RunSummary,
    UnmatchedItem,
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

        log.info(
            "sync.data_type.start",
            message=f"Planning {data_type.value} changes",
            data_type=data_type.value,
        )

        plan = await reconciler.plan(ctx)
        summary.planned += len(plan.changes)
        summary.matched += _count_matched(plan.changes)
        await _collect_unmatched(ctx, data_type, summary)

        log.info(
            "sync.data_type.done",
            message=f"Planned {len(plan.changes)} {data_type.value} change(s)",
            data_type=data_type.value,
            planned=len(plan.changes),
            matched=_count_matched(plan.changes),
        )

        for change in plan.changes:
            prefix = "would" if ctx.dry_run else "will"
            plan_fields: dict[str, object] = {
                "data_type": data_type.value,
                "action": change.action.value,
                "target": change.target_source,
                "title": change.item.title,
                "message": f"{prefix} {change.message}",
                "dry_run": ctx.dry_run,
            }
            if change.field == "rating" and change.new_value is not None:
                plan_fields["rating"] = change.new_value
            log.info("sync.plan", **plan_fields)

        if not plan.changes:
            continue

        grouped = _group_by_target_and_action(plan.changes)
        for (target_name, action), changes in grouped.items():
            source = ctx.sources.get(target_name)
            if source is None:
                summary.errors += len(changes)
                continue

            if ctx.dry_run:
                start_message = (
                    f"Dry-run: would apply {len(changes)} {data_type.value} "
                    f"change(s) ({action.value}) to {target_name}"
                )
            else:
                start_message = (
                    f"Applying {len(changes)} {data_type.value} change(s) ({action.value}) to {target_name}"
                )
            log.info(
                "sync.apply.start",
                message=start_message,
                target=target_name,
                data_type=data_type.value,
                action=action.value,
                count=len(changes),
                dry_run=ctx.dry_run,
            )

            try:
                result = await _apply_changes(source, data_type, changes, dry_run=ctx.dry_run)
            except Exception as exc:
                log.warning(
                    "sync.apply.failed",
                    message=(
                        f"Failed applying {len(changes)} {data_type.value} change(s) to {target_name}: {exc}"
                    ),
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

            error_suffix = f" ({result.errors} error(s))" if result.errors else ""
            if ctx.dry_run:
                done_message = (
                    f"Dry-run: would apply {result.applied}/{len(changes)} "
                    f"{data_type.value} change(s) to {target_name}{error_suffix}"
                )
            else:
                done_message = (
                    f"Applied {result.applied}/{len(changes)} "
                    f"{data_type.value} change(s) to {target_name}{error_suffix}"
                )
            log.info(
                "sync.apply.done",
                message=done_message,
                target=target_name,
                data_type=data_type.value,
                action=action.value,
                applied=result.applied,
                errors=result.errors,
                dry_run=ctx.dry_run,
            )

            _merge_summary(summary, data_type, action, result, changes)

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
    changes: list[PlannedChange],
) -> None:
    from plextraktbox.sync.media_item import MediaType

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

    # TV breakdown — only when the whole batch applied (incl. dry-run).
    if result.applied == len(changes) and changes:
        if data_type == DataType.WATCHLIST and action == ChangeAction.ADD:
            summary.shows_added += sum(1 for change in changes if change.item.media_type == MediaType.SHOW)
        elif data_type == DataType.WATCHLIST and action == ChangeAction.REMOVE:
            summary.shows_removed += sum(1 for change in changes if change.item.media_type == MediaType.SHOW)
        elif data_type == DataType.WATCHED and action == ChangeAction.UPDATE:
            summary.episodes_watched += sum(
                1 for change in changes if change.item.media_type == MediaType.EPISODE
            )


async def _collect_unmatched(ctx: SyncContext, data_type: DataType, summary: RunSummary) -> None:
    """Record fetched items missing identifiers or cross-service matches."""
    seen: set[tuple[str, str, str]] = set()

    def add(item: object, *, source: str, reason: str) -> None:
        from plextraktbox.sync.media_item import MediaItem

        if not isinstance(item, MediaItem):
            return
        key = (source, data_type.value, item.source_key or item.title)
        if key in seen:
            return
        seen.add(key)
        summary.unmatched.append(
            UnmatchedItem(
                source=source,
                data_type=data_type.value,
                title=item.title,
                source_key=item.source_key or item.match_key() or item.title,
                reason=reason,
            )
        )

    for source_name in ctx.source_names():
        items = await ctx.fetch(source_name, data_type)
        for item in items:
            if not item.identifiers:
                add(item, source=source_name, reason="missing identifiers")

    if data_type == DataType.WATCHLIST and "plex" in ctx.sources and "trakt" in ctx.sources:
        truth = [i for i in await ctx.fetch("plex", data_type) if i.watchlisted]
        target = [i for i in await ctx.fetch("trakt", data_type) if i.watchlisted]
        matcher = MediaMatcher()
        matcher.add_many(target)
        for item in truth:
            if item.identifiers and matcher.find(item) is None:
                add(item, source="plex", reason="no trakt match")

    if data_type == DataType.RATINGS and "letterboxd" in ctx.sources:
        truth = [i for i in await ctx.fetch("letterboxd", data_type) if i.rating is not None]
        for target_name in ("plex", "trakt"):
            if target_name not in ctx.sources:
                continue
            target_items = await ctx.fetch(target_name, data_type)
            matcher = MediaMatcher()
            matcher.add_many(target_items)
            for item in truth:
                if not item.identifiers or matcher.find(item) is not None:
                    continue
                if target_name == "plex":
                    continue
                add(item, source="letterboxd", reason=f"no {target_name} match")

    if data_type == DataType.WATCHED and "trakt" in ctx.sources and "plex" in ctx.sources:
        truth = [i for i in await ctx.fetch("trakt", data_type) if i.watched]
        target_items = await ctx.fetch("plex", data_type)
        matcher = MediaMatcher()
        matcher.add_many(target_items)
        for item in truth:
            if item.identifiers and matcher.find(item) is None:
                add(item, source="trakt", reason="no plex match")
