"""In-process pub/sub for live run log streaming."""

from __future__ import annotations

import asyncio
import contextlib
import threading
from collections import deque
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any, Literal

RING_BUFFER_SIZE = 500


@dataclass(frozen=True, slots=True)
class StreamLogEvent:
    type: Literal["log"] = "log"
    id: int = 0
    run_id: int = 0
    ts: str = ""
    level: str = "info"
    logger: str = ""
    message: str = ""
    context: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class StreamEndEvent:
    type: Literal["end"] = "end"
    status: str = "success"


StreamEvent = StreamLogEvent | StreamEndEvent


class RunChannel:
    """Per-run ring buffer plus subscriber queues for SSE clients."""

    def __init__(self, run_id: int) -> None:
        self.run_id = run_id
        self._ring: deque[StreamLogEvent] = deque(maxlen=RING_BUFFER_SIZE)
        self._subscribers: list[asyncio.Queue[StreamEvent | None]] = []
        self._lock = threading.Lock()
        self._closed = False
        self._end_status: str | None = None
        self._loop: asyncio.AbstractEventLoop | None = None

    def set_event_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

    def publish(self, event: StreamLogEvent) -> None:
        with self._lock:
            if self._closed:
                return
            self._ring.append(event)
            subscribers = list(self._subscribers)

        for queue in subscribers:
            self._put_threadsafe(queue, event)

    def backlog(self, *, after_id: int = 0) -> list[StreamLogEvent]:
        with self._lock:
            return [event for event in self._ring if event.id > after_id]

    def subscribe(self) -> asyncio.Queue[StreamEvent | None]:
        queue: asyncio.Queue[StreamEvent | None] = asyncio.Queue()
        with self._lock:
            self._subscribers.append(queue)
            if self._closed and self._end_status is not None:
                end = StreamEndEvent(status=self._end_status)
                self._put_threadsafe(queue, end)
                self._put_threadsafe(queue, None)
        return queue

    def unsubscribe(self, queue: asyncio.Queue[StreamEvent | None]) -> None:
        with self._lock, contextlib.suppress(ValueError):
            self._subscribers.remove(queue)

    def close(self, status: str) -> None:
        end = StreamEndEvent(status=status)
        with self._lock:
            if self._closed:
                return
            self._closed = True
            self._end_status = status
            subscribers = list(self._subscribers)

        for queue in subscribers:
            self._put_threadsafe(queue, end)
            self._put_threadsafe(queue, None)

    @property
    def closed(self) -> bool:
        with self._lock:
            return self._closed

    @property
    def end_status(self) -> str | None:
        with self._lock:
            return self._end_status

    def _put_threadsafe(self, queue: asyncio.Queue[StreamEvent | None], item: StreamEvent | None) -> None:
        loop = self._loop
        if loop is None or not loop.is_running():
            with contextlib.suppress(asyncio.QueueFull):
                queue.put_nowait(item)
            return
        loop.call_soon_threadsafe(queue.put_nowait, item)


class LogHub:
    """Registry of active and recently completed run channels."""

    def __init__(self) -> None:
        self._channels: dict[int, RunChannel] = {}
        self._lock = threading.Lock()
        self._loop: asyncio.AbstractEventLoop | None = None

    def set_event_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop
        with self._lock:
            for channel in self._channels.values():
                channel.set_event_loop(loop)

    def open(self, run_id: int) -> RunChannel:
        with self._lock:
            channel = self._channels.get(run_id)
            if channel is None:
                channel = RunChannel(run_id)
                if self._loop is not None:
                    channel.set_event_loop(self._loop)
                self._channels[run_id] = channel
            return channel

    def get(self, run_id: int) -> RunChannel | None:
        with self._lock:
            return self._channels.get(run_id)

    def close(self, run_id: int, *, status: str) -> None:
        channel = self.get(run_id)
        if channel is not None:
            channel.close(status)

    async def iter_events(
        self,
        run_id: int,
        *,
        after_id: int = 0,
    ) -> AsyncIterator[StreamEvent]:
        channel = self.get(run_id)
        if channel is None:
            return

        for event in channel.backlog(after_id=after_id):
            yield event

        if channel.closed:
            if channel.end_status is not None:
                yield StreamEndEvent(status=channel.end_status)
            return

        queue = channel.subscribe()
        try:
            while True:
                live_event: StreamEvent | None = await queue.get()
                if live_event is None:
                    break
                yield live_event
                if live_event.type == "end":
                    break
        finally:
            channel.unsubscribe(queue)


_hub: LogHub | None = None
_hub_lock = threading.Lock()


def get_log_hub() -> LogHub:
    global _hub
    with _hub_lock:
        if _hub is None:
            _hub = LogHub()
        return _hub
