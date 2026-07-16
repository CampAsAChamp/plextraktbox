"""Cooperative cancellation for in-flight sync runs."""

from __future__ import annotations

import threading
from contextvars import ContextVar, Token

_cancel_events: dict[int, threading.Event] = {}
_cancel_guard = threading.Lock()
_active_cancel_event: ContextVar[threading.Event | None] = ContextVar("sync_cancel_event", default=None)


class RunCancelled(Exception):
    """Raised when a sync run should stop at the next safe checkpoint."""


def register_cancel_event(run_id: int) -> threading.Event:
    """Create (or replace) a cancel event for a run; returns the event."""
    event = threading.Event()
    with _cancel_guard:
        _cancel_events[run_id] = event
    return event


def get_cancel_event(run_id: int) -> threading.Event | None:
    with _cancel_guard:
        return _cancel_events.get(run_id)


def request_cancel(run_id: int) -> bool:
    """Signal cancel for a registered run. Returns True if an event existed."""
    with _cancel_guard:
        event = _cancel_events.get(run_id)
    if event is None:
        return False
    event.set()
    return True


def clear_cancel_event(run_id: int) -> None:
    with _cancel_guard:
        _cancel_events.pop(run_id, None)


def set_active_cancel_event(event: threading.Event | None) -> Token[threading.Event | None]:
    """Bind the cancel event for the current context (apply_live reads it)."""
    return _active_cancel_event.set(event)


def reset_active_cancel_event(token: Token[threading.Event | None]) -> None:
    _active_cancel_event.reset(token)


def active_cancel_event() -> threading.Event | None:
    return _active_cancel_event.get()


def check_cancelled(event: threading.Event | None = None) -> None:
    """Raise RunCancelled if the given or active cancel event is set."""
    resolved = event if event is not None else active_cancel_event()
    if resolved is not None and resolved.is_set():
        raise RunCancelled("Cancelled by user")
