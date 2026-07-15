"""Watchlist reconciler — Plex is source of truth."""

from __future__ import annotations

import pytest

from plextraktbox.sync.engine import run_sync
from plextraktbox.sync.plans import DataType
from plextraktbox.sync.reconcilers.watchlist import WatchlistReconciler
from tests.fakes import FakeLetterboxd, FakePlex, FakeTrakt, movie
from tests.sync_helpers import make_context


@pytest.mark.asyncio
async def test_adds_missing_trakt_watchlist_items() -> None:
    plex, trakt = FakePlex(), FakeTrakt()
    plex.seed_watchlist([movie(title="The Matrix", tmdb="603", watchlisted=True, source="plex")])
    trakt.seed_watchlist([])

    ctx = make_context(
        sources={"plex": plex, "trakt": trakt},
        data_types={DataType.WATCHLIST},
        dry_run=False,
    )
    plan = await WatchlistReconciler().plan(ctx)
    assert len(plan.changes) == 1
    assert plan.changes[0].target_source == "trakt"

    summary = await run_sync(ctx)
    assert summary.added == 1
    trakt_items = await trakt.fetch_watchlist()
    assert len(trakt_items) == 1
    assert trakt_items[0].identifiers["tmdb"] == "603"


@pytest.mark.asyncio
async def test_removes_extra_trakt_watchlist_items() -> None:
    plex, trakt = FakePlex(), FakeTrakt()
    plex.seed_watchlist([])
    trakt.seed_watchlist([movie(title="Extra", tmdb="999", watchlisted=True, source="trakt")])

    ctx = make_context(
        sources={"plex": plex, "trakt": trakt},
        data_types={DataType.WATCHLIST},
        dry_run=False,
    )
    summary = await run_sync(ctx)
    assert summary.removed == 1
    assert len(await trakt.fetch_watchlist()) == 0


@pytest.mark.asyncio
async def test_dry_run_makes_no_writes() -> None:
    plex, trakt = FakePlex(), FakeTrakt()
    plex.seed_watchlist([movie(title="The Matrix", tmdb="603", watchlisted=True, source="plex")])
    trakt.seed_watchlist([])

    ctx = make_context(
        sources={"plex": plex, "trakt": trakt},
        data_types={DataType.WATCHLIST},
        dry_run=True,
    )
    summary = await run_sync(ctx)
    assert summary.planned == 1
    assert summary.added == 1  # counted as would-apply
    assert len(await trakt.fetch_watchlist()) == 0


@pytest.mark.asyncio
async def test_letterboxd_watchlist_never_drives_plan() -> None:
    """Even if Letterboxd is present in context, its watchlist is ignored."""
    plex, trakt, lb = FakePlex(), FakeTrakt(), FakeLetterboxd()
    plex.seed_watchlist([movie(title="Plex pick", tmdb="1", watchlisted=True, source="plex")])
    lb.seed_watchlist([movie(title="LB-only", tmdb="2", watchlisted=True, source="letterboxd")])

    ctx = make_context(
        sources={"plex": plex, "trakt": trakt, "letterboxd": lb},
        data_types={DataType.WATCHLIST},
        dry_run=False,
    )
    plan = await WatchlistReconciler().plan(ctx)
    assert len(plan.changes) == 1
    assert plan.changes[0].item.identifiers["tmdb"] == "1"

    summary = await run_sync(ctx)
    assert summary.added == 1
    trakt_items = await trakt.fetch_watchlist()
    assert len(trakt_items) == 1
    assert trakt_items[0].identifiers["tmdb"] == "1"
    assert len(await lb.fetch_watchlist()) == 1
