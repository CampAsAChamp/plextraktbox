"""Run log pipeline unit tests."""

from __future__ import annotations

import asyncio

from plextraktbox.logstream.handler import LogRecord, _redact_context, run_log_processor
from plextraktbox.logstream.pubsub import StreamLogEvent, get_log_hub


def test_redact_context_masks_sensitive_keys() -> None:
    context = {
        "token": "abc123",
        "api_key": "secret",
        "title": "Inception",
    }

    redacted = _redact_context(context)

    assert redacted["token"] == "***"
    assert redacted["api_key"] == "***"
    assert redacted["title"] == "Inception"


def test_run_log_processor_ignores_events_without_run_id() -> None:
    event_dict = {"event": "sync.plan", "level": "info"}

    result = run_log_processor(None, "info", event_dict)

    assert result == event_dict


def test_run_channel_backlog_and_close() -> None:
    hub = get_log_hub()
    channel = hub.open(42)
    loop = asyncio.new_event_loop()
    channel.set_event_loop(loop)

    event = StreamLogEvent(
        id=1,
        run_id=42,
        ts="2026-01-01T00:00:00+00:00",
        level="info",
        logger="sync.engine",
        message="hello",
        context={"title": "Test"},
    )
    channel.publish(event)
    assert channel.backlog() == [event]

    channel.close(status="success")
    assert channel.closed is True
    assert channel.end_status == "success"

    # Closed channels ignore new events.
    channel.publish(
        StreamLogEvent(
            id=2,
            run_id=42,
            ts="2026-01-01T00:00:01+00:00",
            level="info",
            logger="sync.engine",
            message="ignored",
        )
    )
    assert len(channel.backlog()) == 1


def test_log_record_dataclass() -> None:
    record = LogRecord(run_id=1, level="info", logger="runner", message="started")

    assert record.run_id == 1
    assert record.message == "started"
