"""pluggy hook specifications for extending the sync engine."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pluggy

if TYPE_CHECKING:
    from plextraktbox.sync.context import SyncContext
    from plextraktbox.sync.plans import RunSummary
    from plextraktbox.sync.reconcilers.base import Reconciler
    from plextraktbox.sync.sources.base import Source

PLUGIN_NAMESPACE = "plextraktbox.sync"

hookspec = pluggy.HookspecMarker(PLUGIN_NAMESPACE)
hookimpl = pluggy.HookimplMarker(PLUGIN_NAMESPACE)


@hookspec
def provide_sources() -> dict[str, Source]:
    """Return additional named sources."""
    return {}


@hookspec
def provide_reconcilers() -> list[Reconciler]:
    """Return additional reconcilers."""
    return []


@hookspec
def before_run(ctx: SyncContext) -> None:
    """Called once before fetching data."""


@hookspec
def after_item(
    ctx: SyncContext,
    *,
    data_type: str,
    message: str,
    error: Exception | None = None,
) -> None:
    """Called after each applied change (or error)."""


@hookspec
def after_run(ctx: SyncContext, summary: RunSummary) -> None:
    """Called once after the run completes."""


def get_plugin_manager() -> pluggy.PluginManager:
    import sys

    pm = pluggy.PluginManager(PLUGIN_NAMESPACE)
    pm.add_hookspecs(sys.modules[__name__])
    return pm
