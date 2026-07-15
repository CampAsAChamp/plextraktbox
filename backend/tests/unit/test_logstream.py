"""Run log pipeline unit tests."""

from __future__ import annotations

import asyncio
from unittest.mock import MagicMock, patch

import structlog

from plextraktbox.logstream.handler import (
    LogRecord,
    _redact_context,
    redact_log_processor,
    run_log_processor,
)
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


def test_redact_context_masks_nested_and_extended_keys() -> None:
    context = {
        "nested": {"refresh_token": "r1", "client_secret": "s1", "title": "Film"},
        "pin_code": "1234",
        "device_code": "ABCD",
        "cookie": "session=x",
        "csrf_token": "csrf",
        "webhook_url": "https://example.com/hook",
        "items": [{"access_token": "a1", "name": "ok"}, "plain"],
    }

    redacted = _redact_context(context)

    assert redacted["nested"] == {"refresh_token": "***", "client_secret": "***", "title": "Film"}
    assert redacted["pin_code"] == "***"
    assert redacted["device_code"] == "***"
    assert redacted["cookie"] == "***"
    assert redacted["csrf_token"] == "***"
    assert redacted["webhook_url"] == "***"
    assert redacted["items"] == [{"access_token": "***", "name": "ok"}, "plain"]


def test_redact_log_processor_mutates_event_dict() -> None:
    event_dict = {
        "event": "sync.plan",
        "level": "info",
        "access_token": "plaintext",
        "title": "Inception",
    }

    result = redact_log_processor(None, "info", event_dict)

    assert result is event_dict
    assert event_dict["access_token"] == "***"
    assert event_dict["title"] == "Inception"
    assert event_dict["event"] == "sync.plan"


def test_run_log_processor_persists_already_redacted_context() -> None:
    event_dict = {
        "event": "sync.plan",
        "level": "info",
        "run_id": 9,
        "access_token": "plaintext",
        "title": "Inception",
    }
    redact_log_processor(None, "info", event_dict)

    writer = MagicMock()
    with patch("plextraktbox.logstream.handler.get_log_writer", return_value=writer):
        run_log_processor(None, "info", event_dict)

    writer.emit.assert_called_once()
    record = writer.emit.call_args.args[0]
    assert record.context["access_token"] == "***"
    assert record.context["title"] == "Inception"


def test_run_log_processor_ignores_events_without_run_id() -> None:
    event_dict = {"event": "sync.plan", "level": "info"}

    result = run_log_processor(None, "info", event_dict)

    assert result == event_dict


def test_run_log_processor_persists_when_run_id_comes_from_contextvars() -> None:
    """Client loggers (e.g. plex apply progress) bind via contextvars, not logger.bind()."""
    structlog.contextvars.bind_contextvars(job_id=7, run_id=42)
    try:
        event_dict = structlog.contextvars.merge_contextvars(
            None,
            "info",
            {"event": "sync.apply.plex.rate", "level": "info", "message": 'rated "Film"'},
        )
        assert event_dict["run_id"] == 42

        writer = MagicMock()
        with patch("plextraktbox.logstream.handler.get_log_writer", return_value=writer):
            run_log_processor(None, "info", event_dict)

        writer.emit.assert_called_once()
        record = writer.emit.call_args.args[0]
        assert record.run_id == 42
        assert record.message == "sync.apply.plex.rate"
    finally:
        structlog.contextvars.unbind_contextvars("job_id", "run_id")


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
