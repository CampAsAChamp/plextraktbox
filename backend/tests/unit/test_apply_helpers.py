"""Apply helper tests."""

from __future__ import annotations

import pytest
from structlog.testing import capture_logs

from plextraktbox.sync.plans import ChangeAction, DataType, PlannedChange
from plextraktbox.sync.sources.apply_helpers import apply_live
from tests.fakes import movie


def _change(title: str) -> PlannedChange:
    return PlannedChange(
        action=ChangeAction.ADD,
        data_type=DataType.WATCHLIST,
        target_source="trakt",
        item=movie(title=title, tmdb="1", watchlisted=True, source="plex"),
        field="watchlisted",
        old_value=False,
        new_value=True,
        message=f"Add {title}",
    )


@pytest.mark.asyncio
async def test_apply_live_dry_run_skips_callback() -> None:
    called = False

    def apply_batch(_changes: list[PlannedChange]) -> None:
        nonlocal called
        called = True

    result = await apply_live([_change("A")], dry_run=True, apply_batch=apply_batch)

    assert result.applied == 1
    assert called is False


@pytest.mark.asyncio
async def test_apply_live_isolates_per_item_failures() -> None:
    def apply_batch(changes: list[PlannedChange]) -> None:
        if len(changes) > 1:
            raise RuntimeError("batch failed")
        if changes[0].item.title == "Bad":
            raise RuntimeError("item failed")

    with capture_logs() as logs:
        result = await apply_live(
            [_change("Good"), _change("Bad"), _change("Also Good")],
            dry_run=False,
            apply_batch=apply_batch,
        )

    assert result.applied == 2
    assert result.errors == 1
    events = {entry["event"] for entry in logs}
    assert "sync.apply.batch_failed" in events
    assert "sync.apply.item_failed" in events
    assert any(entry.get("title") == "Bad" for entry in logs)


@pytest.mark.asyncio
async def test_apply_live_raises_on_cancel() -> None:
    import threading

    from plextraktbox.sync.cancellation import RunCancelled

    event = threading.Event()
    event.set()

    with pytest.raises(RunCancelled):
        await apply_live(
            [_change("A"), _change("B")],
            dry_run=False,
            apply_batch=lambda _c: None,
            cancel_event=event,
        )
