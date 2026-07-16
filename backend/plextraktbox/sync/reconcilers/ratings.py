"""Ratings reconciler — Letterboxd is source of truth."""

from __future__ import annotations

from plextraktbox.sync.context import SyncContext
from plextraktbox.sync.plans import ChangeAction, DataType, PlannedChange, ReconcilePlan
from plextraktbox.sync.reconcilers.base import Reconciler
from plextraktbox.sync.reconcilers.helpers import build_matcher, iter_writable_targets
from plextraktbox.utils.rating import letterboxd_to_normalized

TRUTH_SOURCE = "letterboxd"
TARGET_SOURCES = ("plex", "trakt")
RATING_TOLERANCE = 0.01

__all__ = ["RatingsReconciler", "letterboxd_to_normalized"]


class RatingsReconciler(Reconciler):
    data_type = DataType.RATINGS

    async def plan(self, ctx: SyncContext) -> ReconcilePlan:
        if TRUTH_SOURCE not in ctx.sources:
            return ReconcilePlan(data_type=self.data_type)

        truth_items = [
            item for item in await ctx.fetch(TRUTH_SOURCE, self.data_type) if item.rating is not None
        ]
        changes: list[PlannedChange] = []

        for target_name, _target in iter_writable_targets(
            ctx, TARGET_SOURCES, write_capability="ratings_write"
        ):
            target_items = await ctx.fetch(target_name, self.data_type)
            matcher = build_matcher(target_items)

            for truth_item in truth_items:
                desired = truth_item.rating
                if desired is None:
                    continue

                target_item = matcher.find(truth_item)
                if target_item is None:
                    if target_name != "plex" or not truth_item.identifiers:
                        continue
                    current = None
                else:
                    current = target_item.rating
                    if current is not None and abs(current - desired) < RATING_TOLERANCE:
                        continue

                changes.append(
                    PlannedChange(
                        action=ChangeAction.UPDATE,
                        data_type=self.data_type,
                        target_source=target_name,
                        item=truth_item,
                        field="rating",
                        old_value=current,
                        new_value=desired,
                        message=(f'rate "{truth_item.title}" on {target_name}: {current} → {desired}'),
                    )
                )

        return ReconcilePlan(data_type=self.data_type, changes=changes)
