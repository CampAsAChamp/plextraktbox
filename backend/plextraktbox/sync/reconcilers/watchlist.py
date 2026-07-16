"""Watchlist reconciler — Plex is source of truth."""

from __future__ import annotations

from plextraktbox.sync.context import SyncContext
from plextraktbox.sync.plans import ChangeAction, DataType, PlannedChange, ReconcilePlan
from plextraktbox.sync.reconcilers.base import Reconciler
from plextraktbox.sync.reconcilers.helpers import build_matcher, iter_writable_targets

TRUTH_SOURCE = "plex"
TARGET_SOURCES = ("trakt",)


class WatchlistReconciler(Reconciler):
    data_type = DataType.WATCHLIST

    async def plan(self, ctx: SyncContext) -> ReconcilePlan:
        if TRUTH_SOURCE not in ctx.sources:
            return ReconcilePlan(data_type=self.data_type)

        truth_items = [item for item in await ctx.fetch(TRUTH_SOURCE, self.data_type) if item.watchlisted]
        changes: list[PlannedChange] = []

        # Letterboxd watchlist is ignored (Plex is truth; LB has no write API).

        for target_name, _target in iter_writable_targets(
            ctx, TARGET_SOURCES, write_capability="watchlist_write"
        ):
            target_items = await ctx.fetch(target_name, self.data_type)
            target_watchlisted = [item for item in target_items if item.watchlisted]

            matcher = build_matcher(target_watchlisted)

            for truth_item in truth_items:
                if matcher.find(truth_item) is not None:
                    continue
                changes.append(
                    PlannedChange(
                        action=ChangeAction.ADD,
                        data_type=self.data_type,
                        target_source=target_name,
                        item=truth_item,
                        field="watchlisted",
                        old_value=False,
                        new_value=True,
                        message=f"Add {truth_item.title} to {target_name} watchlist",
                    )
                )

            truth_matcher = build_matcher(truth_items)
            for target_item in target_watchlisted:
                if truth_matcher.find(target_item) is not None:
                    continue
                changes.append(
                    PlannedChange(
                        action=ChangeAction.REMOVE,
                        data_type=self.data_type,
                        target_source=target_name,
                        item=target_item,
                        field="watchlisted",
                        old_value=True,
                        new_value=False,
                        message=f"Remove {target_item.title} from {target_name} watchlist",
                    )
                )

        return ReconcilePlan(data_type=self.data_type, changes=changes)
