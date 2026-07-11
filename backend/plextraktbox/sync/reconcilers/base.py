"""Reconciler base types."""

from __future__ import annotations

from abc import ABC, abstractmethod

from plextraktbox.sync.context import SyncContext
from plextraktbox.sync.plans import DataType, ReconcilePlan


class Reconciler(ABC):
    data_type: DataType

    @abstractmethod
    async def plan(self, ctx: SyncContext) -> ReconcilePlan:
        raise NotImplementedError
