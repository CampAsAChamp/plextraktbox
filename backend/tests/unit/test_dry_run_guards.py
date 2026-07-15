"""Dry-run safety and exclude filter tests."""

from __future__ import annotations

import pytest
from sqlmodel import Session

from plextraktbox.models.job import Job, SourcePair
from plextraktbox.models.job_run import JobRun, JobRunStatus, RunTrigger
from plextraktbox.services.dry_run import resolve_dry_run
from plextraktbox.sync.context import SyncContext
from plextraktbox.sync.excludes import filter_excluded_items, normalize_exclude_ids
from plextraktbox.sync.media_item import MediaItem, MediaType
from plextraktbox.sync.plans import DataType


def test_resolve_dry_run_override_wins(session: Session) -> None:
    job = Job(name="j", source_pair=SourcePair.PLEX_TRAKT, dry_run=False, require_dry_run_first=False)
    session.add(job)
    session.commit()
    session.refresh(job)
    dry_run, coerced = resolve_dry_run(session, job, dry_run_override=True)
    assert dry_run is True
    assert coerced is False


def test_require_dry_run_first_coerces_until_success(session: Session) -> None:
    job = Job(
        name="j",
        source_pair=SourcePair.PLEX_TRAKT,
        dry_run=False,
        require_dry_run_first=True,
    )
    session.add(job)
    session.commit()
    session.refresh(job)

    dry_run, coerced = resolve_dry_run(session, job, dry_run_override=None)
    assert dry_run is True
    assert coerced is True

    run = JobRun(
        job_id=job.id or 0,
        job_name=job.name,
        trigger=RunTrigger.MANUAL,
        dry_run=True,
        status=JobRunStatus.SUCCESS,
    )
    session.add(run)
    session.commit()

    dry_run, coerced = resolve_dry_run(session, job, dry_run_override=None)
    assert dry_run is False
    assert coerced is False


def test_filter_excluded_items() -> None:
    items = [
        MediaItem(title="Keep", media_type=MediaType.MOVIE, identifiers={"tmdb": "1"}),
        MediaItem(title="Drop", media_type=MediaType.MOVIE, identifiers={"imdb": "tt9"}),
    ]
    exclude = normalize_exclude_ids({"imdb": ["tt9"]})
    kept, count = filter_excluded_items(items, exclude)
    assert count == 1
    assert len(kept) == 1
    assert kept[0].title == "Keep"


class _FakeSource:
    name = "fake"

    async def fetch_watchlist(self) -> list[MediaItem]:
        return [
            MediaItem(title="A", media_type=MediaType.MOVIE, identifiers={"tmdb": "1"}),
            MediaItem(title="B", media_type=MediaType.MOVIE, identifiers={"tmdb": "2"}),
        ]

    async def fetch_ratings(self) -> list[MediaItem]:
        return []

    async def fetch_watched(self) -> list[MediaItem]:
        return []


@pytest.mark.asyncio
async def test_sync_context_fetch_applies_excludes() -> None:
    ctx = SyncContext(
        sources={"fake": _FakeSource()},  # type: ignore[dict-item]
        data_types={DataType.WATCHLIST},
        dry_run=True,
        exclude_ids=normalize_exclude_ids({"tmdb": ["2"]}),
    )
    items = await ctx.fetch("fake", DataType.WATCHLIST)
    assert [item.title for item in items] == ["A"]
