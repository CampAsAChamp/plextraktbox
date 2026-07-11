"""Ratings reconciler — Letterboxd is source of truth."""

from __future__ import annotations

import pytest

from plextraktbox.sync.engine import run_sync
from plextraktbox.sync.plans import DataType
from plextraktbox.sync.reconcilers.ratings import RatingsReconciler, letterboxd_to_normalized
from tests.fakes import FakeLetterboxd, FakePlex, movie
from tests.sync_helpers import make_context


def test_letterboxd_rating_normalization() -> None:
    assert letterboxd_to_normalized(4.5) == 9.0
    assert letterboxd_to_normalized(2.5) == 5.0


@pytest.mark.asyncio
async def test_pushes_lb_rating_to_plex() -> None:
    lb, plex = FakeLetterboxd(), FakePlex()
    lb.seed_ratings([movie(title="The Matrix", tmdb="603", rating=9.0, source="letterboxd")])
    plex.seed_ratings([movie(title="The Matrix", tmdb="603", rating=6.0, source="plex")])

    ctx = make_context(
        sources={"letterboxd": lb, "plex": plex},
        data_types={DataType.RATINGS},
        dry_run=False,
    )
    plan = await RatingsReconciler().plan(ctx)
    assert len(plan.changes) == 1
    assert plan.changes[0].new_value == 9.0

    summary = await run_sync(ctx)
    assert summary.rated == 1
    plex_items = await plex.fetch_ratings()
    assert plex_items[0].rating == 9.0


@pytest.mark.asyncio
async def test_dry_run_leaves_plex_rating_unchanged() -> None:
    lb, plex = FakeLetterboxd(), FakePlex()
    lb.seed_ratings([movie(title="The Matrix", tmdb="603", rating=10.0, source="letterboxd")])
    plex.seed_ratings([movie(title="The Matrix", tmdb="603", rating=6.0, source="plex")])

    ctx = make_context(
        sources={"letterboxd": lb, "plex": plex},
        data_types={DataType.RATINGS},
        dry_run=True,
    )
    await run_sync(ctx)
    plex_items = await plex.fetch_ratings()
    assert plex_items[0].rating == 6.0
