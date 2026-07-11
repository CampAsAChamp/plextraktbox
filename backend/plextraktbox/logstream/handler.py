"""structlog processor and background writer for run log persistence."""

from __future__ import annotations

import json
import queue
import re
import threading
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

import structlog
from sqlmodel import Session

from plextraktbox import db
from plextraktbox.logstream.pubsub import StreamLogEvent, get_log_hub
from plextraktbox.models.log_entry import LogEntry
from plextraktbox.utils.datetime import serialize_utc_datetime

_REDACT_KEY = re.compile(r"(token|password|secret|api_key|authorization|credential)", re.I)
_STANDARD_KEYS = frozenset(
    {
        "event",
        "level",
        "timestamp",
        "logger",
        "logger_name",
        "run_id",
        "job_id",
        "exc_info",
        "stack_info",
    }
)


@dataclass(slots=True)
class LogRecord:
    run_id: int
    level: str
    logger: str
    message: str
    context: dict[str, Any] = field(default_factory=dict)
    ts: datetime | None = None


def _redact_value(key: str, value: object) -> object:
    if _REDACT_KEY.search(key):
        return "***"
    if isinstance(value, dict):
        return {k: _redact_value(str(k), v) for k, v in value.items()}
    if isinstance(value, list):
        return [_redact_value(key, item) for item in value]
    return value


def _redact_context(context: dict[str, Any]) -> dict[str, Any]:
    return {key: _redact_value(key, value) for key, value in context.items()}


def _serialize_context(context: dict[str, Any]) -> dict[str, Any]:
    redacted = _redact_context(context)

    def _default(value: object) -> str:
        return repr(value)

    try:
        json.dumps(redacted, default=_default)
    except TypeError:
        return {key: repr(value) for key, value in redacted.items()}
    return redacted


class LogWriter:
    """Background thread that persists run logs and publishes to live subscribers."""

    def __init__(self) -> None:
        self._queue: queue.Queue[LogRecord | None] = queue.Queue()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread is not None:
            return
        self._thread = threading.Thread(target=self._run, name="log-writer", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if self._thread is None:
            return
        self._queue.put(None)
        self._thread.join(timeout=5)
        self._thread = None

    def emit(self, record: LogRecord) -> None:
        self._queue.put(record)

    def _run(self) -> None:
        while True:
            item = self._queue.get()
            if item is None:
                break
            self._persist_and_publish(item)

    def _persist_and_publish(self, record: LogRecord) -> None:
        ts = record.ts or datetime.now(UTC)
        context = _serialize_context(record.context)
        entry = LogEntry(
            run_id=record.run_id,
            ts=ts,
            level=record.level,
            logger=record.logger,
            message=record.message,
        )
        entry.set_context(context)

        with Session(db.engine) as session:
            session.add(entry)
            session.commit()
            session.refresh(entry)

        if entry.id is None:
            return

        event = StreamLogEvent(
            id=entry.id,
            run_id=entry.run_id,
            ts=serialize_utc_datetime(entry.ts),
            level=entry.level,
            logger=entry.logger,
            message=entry.message,
            context=context,
        )
        channel = get_log_hub().get(record.run_id)
        if channel is not None:
            channel.publish(event)


_writer: LogWriter | None = None
_writer_lock = threading.Lock()


def get_log_writer() -> LogWriter:
    global _writer
    with _writer_lock:
        if _writer is None:
            _writer = LogWriter()
        return _writer


def run_log_processor(
    _logger: object,
    method_name: str,
    event_dict: structlog.types.EventDict,
) -> structlog.types.EventDict:
    """Persist and publish logs that include a ``run_id`` binding."""
    run_id = event_dict.get("run_id")
    if run_id is None:
        return event_dict

    try:
        run_id_int = int(run_id)
    except TypeError, ValueError:
        return event_dict

    message = event_dict.get("event")
    if not isinstance(message, str):
        message = str(message)

    level = event_dict.get("level")
    if not isinstance(level, str):
        level = method_name

    logger_name = event_dict.get("logger") or event_dict.get("logger_name") or ""
    if not isinstance(logger_name, str):
        logger_name = str(logger_name)

    context = {
        key: value
        for key, value in event_dict.items()
        if key not in _STANDARD_KEYS and not key.startswith("_")
    }

    ts_raw = event_dict.get("timestamp")
    ts: datetime | None
    if isinstance(ts_raw, str):
        try:
            ts = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
        except ValueError:
            ts = None
    else:
        ts = None

    get_log_writer().emit(
        LogRecord(
            run_id=run_id_int,
            level=level.lower(),
            logger=logger_name,
            message=message,
            context=context,
            ts=ts,
        )
    )
    return event_dict
