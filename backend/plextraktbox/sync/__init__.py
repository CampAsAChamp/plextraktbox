"""Sync engine: sources, reconcilers, and orchestration."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

__all__ = ["RunSummary", "run_sync"]

if TYPE_CHECKING:
    from plextraktbox.sync.engine import run_sync as run_sync
    from plextraktbox.sync.plans import RunSummary as RunSummary


def __getattr__(name: str) -> Any:
    if name == "run_sync":
        from plextraktbox.sync.engine import run_sync

        return run_sync
    if name == "RunSummary":
        from plextraktbox.sync.plans import RunSummary

        return RunSummary
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
