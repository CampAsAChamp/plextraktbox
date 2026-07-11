"""Ratings reconciler — Letterboxd is source of truth."""

from __future__ import annotations

from plextraktbox.sync.context import SyncContext
from plextraktbox.sync.matcher import MediaMatcher
from plextraktbox.sync.plans import ChangeAction, DataType, PlannedChange, ReconcilePlan
from plextraktbox.sync.reconcilers.base import Reconciler

TRUTH_SOURCE = "letterboxd"
TARGET_SOURCES = ("plex", "trakt")
RATING_TOLERANCE = 0.01


def letterboxd_to_normalized(stars: float) -> float:
    """Convert Letterboxd 0.5–5 stars to Plex/Trakt 0–10 scale."""
    return round(stars * 2, 1)


class RatingsReconciler(Reconciler):
    data_type = DataType.RATINGS

    async def plan(self, ctx: SyncContext) -> ReconcilePlan:
        if TRUTH_SOURCE not in ctx.sources:
            return ReconcilePlan(data_type=self.data_type)

        truth_items = [
            item for item in await ctx.fetch(TRUTH_SOURCE, self.data_type) if item.rating is not None
        ]
        changes: list[PlannedChange] = []

        for target_name in TARGET_SOURCES:
            if target_name not in ctx.sources:
                continue
            target = ctx.sources[target_name]
            if not target.capabilities.ratings_write:
                continue

            target_items = await ctx.fetch(target_name, self.data_type)
            matcher = MediaMatcher()
            matcher.add_many(target_items)

            for truth_item in truth_items:
                target_item = matcher.find(truth_item)
                if target_item is None:
                    continue
                desired = truth_item.rating
                if desired is None:
                    continue
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
                        message=(f"Rate {truth_item.title} on {target_name}: {current} → {desired}"),
                    )
                )

        return ReconcilePlan(data_type=self.data_type, changes=changes)
