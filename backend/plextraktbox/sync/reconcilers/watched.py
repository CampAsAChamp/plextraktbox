"""Watched reconciler — Trakt is source of truth."""

from __future__ import annotations

from plextraktbox.sync.context import SyncContext
from plextraktbox.sync.matcher import MediaMatcher
from plextraktbox.sync.plans import ChangeAction, DataType, PlannedChange, ReconcilePlan
from plextraktbox.sync.reconcilers.base import Reconciler

TRUTH_SOURCE = "trakt"
TARGET_SOURCES = ("plex",)


class WatchedReconciler(Reconciler):
    data_type = DataType.WATCHED

    async def plan(self, ctx: SyncContext) -> ReconcilePlan:
        if TRUTH_SOURCE not in ctx.sources:
            return ReconcilePlan(data_type=self.data_type)

        truth_items = [item for item in await ctx.fetch(TRUTH_SOURCE, self.data_type) if item.watched]
        changes: list[PlannedChange] = []

        for target_name in TARGET_SOURCES:
            if target_name not in ctx.sources:
                continue
            target = ctx.sources[target_name]
            if not target.capabilities.watched_write:
                continue

            target_items = await ctx.fetch(target_name, self.data_type)
            matcher = MediaMatcher()
            matcher.add_many(target_items)

            for truth_item in truth_items:
                target_item = matcher.find(truth_item)
                if target_item is None:
                    continue
                if target_item.watched:
                    continue
                changes.append(
                    PlannedChange(
                        action=ChangeAction.UPDATE,
                        data_type=self.data_type,
                        target_source=target_name,
                        item=truth_item,
                        field="watched",
                        old_value=False,
                        new_value=True,
                        message=f"Mark {truth_item.title} watched on {target_name}",
                    )
                )

        return ReconcilePlan(data_type=self.data_type, changes=changes)
