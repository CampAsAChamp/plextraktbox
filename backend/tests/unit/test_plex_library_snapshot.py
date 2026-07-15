"""Once-per-run Plex library snapshot sharing (Phase 21)."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from structlog.testing import capture_logs

from plextraktbox.clients import plex_client
from plextraktbox.sync.media_item import MediaItem, MediaType
from plextraktbox.sync.plans import ChangeAction, DataType, PlannedChange
from plextraktbox.sync.sources.plex_source import PlexSource


def _movie(*, tmdb: str = "603", title: str = "The Matrix") -> MediaItem:
    return MediaItem(
        title=title,
        media_type=MediaType.MOVIE,
        identifiers={"tmdb": tmdb},
    )


def _library_video(*, tmdb: str = "603", title: str = "The Matrix") -> SimpleNamespace:
    video = SimpleNamespace(
        type="movie",
        title=title,
        ratingKey="1",
        guid=f"tmdb://{tmdb}",
        guids=[],
        userRating=None,
        viewCount=0,
        lastViewedAt=None,
        isWatched=False,
        rate_calls=[],
    )
    video.rate = lambda rating: video.rate_calls.append(rating) or video  # type: ignore[method-assign]
    return video


@pytest.mark.asyncio
async def test_plex_source_loads_movies_once_for_fetch_and_apply(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    video = _library_video()
    fetch_calls = 0

    def fake_fetch(
        url: str,
        token: str,
        *,
        library_type: str,
        library_ids: list[str] | None = None,
    ) -> list[SimpleNamespace]:
        nonlocal fetch_calls
        fetch_calls += 1
        assert library_type == "movie"
        return [video]

    monkeypatch.setattr(plex_client, "_fetch_library_entries", fake_fetch)

    source = PlexSource(url="http://plex.local:32400", token="plex-token")

    with capture_logs() as logs:
        items = await source.fetch_ratings()
        result = await source.apply_ratings(
            [
                PlannedChange(
                    action=ChangeAction.UPDATE,
                    data_type=DataType.RATINGS,
                    target_source="plex",
                    item=_movie(),
                    field="rating",
                    old_value=0.0,
                    new_value=9.0,
                    message="Rate The Matrix",
                )
            ],
            dry_run=False,
        )

    assert len(items) == 1
    assert items[0].identifiers["tmdb"] == "603"
    assert result.applied == 1
    assert result.errors == 0
    assert fetch_calls == 1
    assert video.rate_calls == [9.0]
    loaded = [entry for entry in logs if entry["event"] == "sync.plex.library.loaded"]
    assert len(loaded) == 1
    assert loaded[0]["library_type"] == "movie"
    assert loaded[0]["count"] == 1


def test_snapshot_movie_index_reuses_loaded_movies(monkeypatch: pytest.MonkeyPatch) -> None:
    video = _library_video()
    fetch_calls = 0

    def fake_fetch(*_args: object, **_kwargs: object) -> list[SimpleNamespace]:
        nonlocal fetch_calls
        fetch_calls += 1
        return [video]

    monkeypatch.setattr(plex_client, "_fetch_library_entries", fake_fetch)

    snapshot = plex_client.PlexLibrarySnapshot(
        url="http://plex.local:32400",
        token="plex-token",
    )
    first = snapshot.movies()
    second = snapshot.movies()
    index = snapshot.movie_index()

    assert first is second
    assert fetch_calls == 1
    assert index["tmdb:603"] is video
