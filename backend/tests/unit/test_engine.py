"""End-to-end sync engine tests."""

from __future__ import annotations

import pytest
from structlog.testing import capture_logs

from plextraktbox.sync.engine import run_sync
from plextraktbox.sync.plans import DataType
from plextraktbox.sync.reconcilers.ratings import letterboxd_to_normalized
from tests.fakes import FakeLetterboxd, FakePlex, FakeTrakt, movie
from tests.sync_helpers import make_context


@pytest.mark.asyncio
async def test_full_plex_trakt_job_respects_dry_run() -> None:
    plex, trakt = FakePlex(), FakeTrakt()
    plex.seed_watchlist([movie(title="A", tmdb="1", watchlisted=True, source="plex")])
    trakt.seed_watched([movie(title="A", tmdb="1", watched=True, source="trakt")])
    plex.seed_watched([movie(title="A", tmdb="1", watched=False, source="plex")])

    ctx = make_context(
        sources={"plex": plex, "trakt": trakt},
        data_types={DataType.WATCHLIST, DataType.WATCHED},
        dry_run=True,
    )
    summary = await run_sync(ctx)
    assert summary.planned >= 2
    assert len(await trakt.fetch_watchlist()) == 0
    assert (await plex.fetch_watched())[0].watched is False


@pytest.mark.asyncio
async def test_ratings_use_normalized_letterboxd_values() -> None:
    lb, plex, trakt = FakeLetterboxd(), FakePlex(), FakeTrakt()
    stars = 4.5
    lb.seed_ratings(
        [movie(title="Film", tmdb="42", rating=letterboxd_to_normalized(stars), source="letterboxd")]
    )
    plex.seed_ratings([movie(title="Film", tmdb="42", rating=0.0, source="plex")])
    trakt.seed_ratings([movie(title="Film", tmdb="42", rating=0.0, source="trakt")])

    ctx = make_context(
        sources={"letterboxd": lb, "plex": plex, "trakt": trakt},
        data_types={DataType.RATINGS},
        dry_run=False,
    )
    summary = await run_sync(ctx)
    assert summary.rated == 2
    assert (await plex.fetch_ratings())[0].rating == 9.0
    assert (await trakt.fetch_ratings())[0].rating == 9.0


@pytest.mark.asyncio
async def test_engine_logs_apply_start_and_done() -> None:
    lb, plex = FakeLetterboxd(), FakePlex()
    lb.seed_ratings([movie(title="Film", tmdb="42", rating=9.0, source="letterboxd")])
    plex.seed_ratings([movie(title="Film", tmdb="42", rating=0.0, source="plex")])

    ctx = make_context(
        sources={"letterboxd": lb, "plex": plex},
        data_types={DataType.RATINGS},
        dry_run=True,
    )
    with capture_logs() as logs:
        await run_sync(ctx)

    events = [entry["event"] for entry in logs]
    assert "sync.apply.start" in events
    assert "sync.apply.done" in events
    start = next(entry for entry in logs if entry["event"] == "sync.apply.start")
    assert start["message"] == "Dry-run: would apply 1 ratings change(s) (update) to plex"
    assert start["count"] == 1
