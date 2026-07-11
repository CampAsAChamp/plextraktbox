"""Run log API schemas."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel

from plextraktbox.models.log_entry import LogEntry
from plextraktbox.utils.datetime import UtcDatetime


class LogEntryItem(BaseModel):
    id: int
    run_id: int
    ts: UtcDatetime
    level: str
    logger: str
    message: str
    context: dict[str, Any]

    @classmethod
    def from_model(cls, entry: LogEntry) -> LogEntryItem:
        return cls(
            id=entry.id or 0,
            run_id=entry.run_id,
            ts=entry.ts,
            level=entry.level,
            logger=entry.logger,
            message=entry.message,
            context=entry.context(),
        )


class LogListResponse(BaseModel):
    items: list[LogEntryItem]
    limit: int
    after_id: int


class StreamLogPayload(BaseModel):
    type: Literal["log"] = "log"
    id: int
    run_id: int
    ts: str
    level: str
    logger: str
    message: str
    context: dict[str, Any]


class StreamEndPayload(BaseModel):
    type: Literal["end"] = "end"
    status: str
