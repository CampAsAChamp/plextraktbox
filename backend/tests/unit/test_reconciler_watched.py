"""Watched reconciler — Trakt is source of truth."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from plextraktbox.sync.engine import run_sync
from plextraktbox.sync.plans import DataType
from tests.fakes import FakePlex, FakeTrakt, episode, movie
from tests.sync_helpers import make_context


@pytest.mark.asyncio
async def test_marks_plex_watched_from_trakt() -> None:
    plex, trakt = FakePlex(), FakeTrakt()
    watched_at = datetime(2024, 1, 15, tzinfo=UTC)
    trakt_item = movie(title="The Matrix", tmdb="603", watched=True, source="trakt")
    trakt_item.watched_at = watched_at
    trakt.seed_watched([trakt_item])
    plex.seed_watched([movie(title="The Matrix", tmdb="603", watched=False, source="plex")])

    ctx = make_context(
        sources={"plex": plex, "trakt": trakt},
        data_types={DataType.WATCHED},
        dry_run=False,
    )
    summary = await run_sync(ctx)
    assert summary.watched == 1
    plex_items = await plex.fetch_watched()
    assert plex_items[0].watched is True


@pytest.mark.asyncio
async def test_dry_run_does_not_mark_plex_watched() -> None:
    plex, trakt = FakePlex(), FakeTrakt()
    trakt.seed_watched([movie(title="The Matrix", tmdb="603", watched=True, source="trakt")])
    plex.seed_watched([movie(title="The Matrix", tmdb="603", watched=False, source="plex")])

    ctx = make_context(
        sources={"plex": plex, "trakt": trakt},
        data_types={DataType.WATCHED},
        dry_run=True,
    )
    await run_sync(ctx)
    plex_items = await plex.fetch_watched()
    assert plex_items[0].watched is False


@pytest.mark.asyncio
async def test_marks_plex_episode_watched_from_trakt() -> None:
    plex, trakt = FakePlex(), FakeTrakt()
    trakt.seed_watched(
        [episode(title="Breaking Bad", season=1, episode=1, tmdb="1396", watched=True, source="trakt")]
    )
    plex.seed_watched(
        [episode(title="Breaking Bad", season=1, episode=1, tmdb="1396", watched=False, source="plex")]
    )

    ctx = make_context(
        sources={"plex": plex, "trakt": trakt},
        data_types={DataType.WATCHED},
        dry_run=False,
    )
    summary = await run_sync(ctx)
    assert summary.watched == 1
    assert summary.episodes_watched == 1
    plex_items = await plex.fetch_watched()
    assert plex_items[0].watched is True


@pytest.mark.asyncio
async def test_episode_without_plex_match_is_skipped() -> None:
    plex, trakt = FakePlex(), FakeTrakt()
    trakt.seed_watched(
        [episode(title="Breaking Bad", season=1, episode=1, tmdb="1396", watched=True, source="trakt")]
    )

    ctx = make_context(
        sources={"plex": plex, "trakt": trakt},
        data_types={DataType.WATCHED},
        dry_run=False,
    )
    summary = await run_sync(ctx)
    assert summary.watched == 0
    assert any(item.reason == "no plex match" for item in summary.unmatched)
