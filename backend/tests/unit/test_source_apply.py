"""Client-backed source apply tests."""

from __future__ import annotations

import pytest
import respx
from httpx import Response

from plextraktbox.sync.plans import ApplyResult, ChangeAction, DataType, PlannedChange
from plextraktbox.sync.sources.base import NotSupported
from plextraktbox.sync.sources.letterboxd_source import LetterboxdSource
from plextraktbox.sync.sources.plex_source import PlexSource
from plextraktbox.sync.sources.trakt_source import TraktSource
from tests.fakes import movie


def _watchlist_add(title: str, *, tmdb: str) -> PlannedChange:
    return PlannedChange(
        action=ChangeAction.ADD,
        data_type=DataType.WATCHLIST,
        target_source="trakt",
        item=movie(title=title, tmdb=tmdb, watchlisted=True, source="plex"),
        field="watchlisted",
        old_value=False,
        new_value=True,
        message=f"Add {title}",
    )


@pytest.mark.asyncio
async def test_trakt_apply_watchlist_dry_run_makes_no_http_calls() -> None:
    source = TraktSource(client_id="client-id", access_token="access-token")
    changes = [_watchlist_add("The Matrix", tmdb="603")]

    with respx.mock:
        respx.post("https://api.trakt.tv/sync/watchlist").mock()
        result = await source.apply_watchlist(changes, dry_run=True)

    assert result == ApplyResult(applied=1)
    assert not respx.calls


@pytest.mark.asyncio
async def test_trakt_apply_watchlist_live_posts_to_trakt() -> None:
    source = TraktSource(client_id="client-id", access_token="access-token")
    changes = [_watchlist_add("The Matrix", tmdb="603")]

    with respx.mock:
        route = respx.post("https://api.trakt.tv/sync/watchlist").mock(
            return_value=Response(200, json={"added": {"movies": 1}, "not_found": {"movies": []}})
        )
        result = await source.apply_watchlist(changes, dry_run=False)

    assert result.applied == 1
    assert route.called


@pytest.mark.asyncio
async def test_plex_apply_ratings_dry_run_makes_no_http_calls(monkeypatch: pytest.MonkeyPatch) -> None:
    called = False

    def fail_apply(*_args, **_kwargs) -> tuple[int, int, int]:
        nonlocal called
        called = True
        return 0, 0, 0

    monkeypatch.setattr("plextraktbox.clients.plex_client.rate_movies_with_discover_fallback", fail_apply)
    source = PlexSource(url="http://plex.local:32400", token="plex-token")
    changes = [
        PlannedChange(
            action=ChangeAction.UPDATE,
            data_type=DataType.RATINGS,
            target_source="plex",
            item=movie(title="Film", tmdb="42", rating=9.0, source="letterboxd"),
            field="rating",
            old_value=0.0,
            new_value=9.0,
            message="Rate Film",
        )
    ]

    result = await source.apply_ratings(changes, dry_run=True)

    assert result.applied == 1
    assert called is False


@pytest.mark.asyncio
async def test_plex_apply_ratings_live_returns_error_counts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "plextraktbox.clients.plex_client.rate_movies_with_discover_fallback",
        lambda *_args, **_kwargs: (1, 0, 1),
    )
    source = PlexSource(url="http://plex.local:32400", token="plex-token")
    changes = [
        PlannedChange(
            action=ChangeAction.UPDATE,
            data_type=DataType.RATINGS,
            target_source="plex",
            item=movie(title="Good", tmdb="1", rating=9.0, source="letterboxd"),
            field="rating",
            old_value=0.0,
            new_value=9.0,
            message="Rate Good",
        ),
        PlannedChange(
            action=ChangeAction.UPDATE,
            data_type=DataType.RATINGS,
            target_source="plex",
            item=movie(title="Bad", tmdb="2", rating=8.0, source="letterboxd"),
            field="rating",
            old_value=0.0,
            new_value=8.0,
            message="Rate Bad",
        ),
    ]

    result = await source.apply_ratings(changes, dry_run=False)

    assert result.applied == 1
    assert result.errors == 1


@pytest.mark.asyncio
async def test_letterboxd_apply_still_unsupported() -> None:
    source = LetterboxdSource(username="user", password="pass")
    changes = [_watchlist_add("Film", tmdb="1")]

    with pytest.raises(NotSupported):
        await source.apply_watchlist(changes, dry_run=False)
