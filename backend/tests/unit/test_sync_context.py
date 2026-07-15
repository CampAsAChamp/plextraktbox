"""SyncContext fetch logging tests."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from plextraktbox.sync.plans import DataType
from tests.fakes import FakeLetterboxd, movie
from tests.sync_helpers import make_context


@pytest.mark.asyncio
async def test_fetch_logs_start_and_done() -> None:
    lb = FakeLetterboxd()
    lb.seed_ratings([movie(title="Film", tmdb="1", rating=9.0, source="letterboxd")])
    log = MagicMock()
    ctx = make_context(
        sources={"letterboxd": lb},
        data_types={DataType.RATINGS},
        dry_run=True,
    )
    ctx.log = log

    items = await ctx.fetch("letterboxd", DataType.RATINGS)

    assert len(items) == 1
    log.info.assert_any_call(
        "sync.fetch.start",
        message="Fetching ratings from letterboxd",
        source="letterboxd",
        data_type="ratings",
    )
    log.info.assert_any_call(
        "sync.fetch.done",
        message="Fetched 1 ratings item(s) from letterboxd (1 with IDs)",
        source="letterboxd",
        data_type="ratings",
        count=1,
        with_ids=1,
        excluded=0,
    )
