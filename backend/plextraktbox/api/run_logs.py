"""Run log REST and SSE endpoints."""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator

from fastapi import APIRouter, HTTPException, Query, status
from sse_starlette.sse import EventSourceResponse

from plextraktbox.api.deps import CurrentUserDep, SessionDep
from plextraktbox.logstream.pubsub import StreamEndEvent, StreamEvent, StreamLogEvent, get_log_hub
from plextraktbox.models.job_run import JobRunStatus
from plextraktbox.schemas.log import LogEntryItem, LogListResponse, StreamEndPayload, StreamLogPayload
from plextraktbox.services import logs as log_svc
from plextraktbox.services import runs as run_svc
from plextraktbox.utils.datetime import serialize_utc_datetime

router = APIRouter(prefix="/runs", tags=["runs"])


@router.get("/{run_id}/logs", response_model=LogListResponse)
def list_run_logs(
    run_id: int,
    _user: CurrentUserDep,
    session: SessionDep,
    after_id: int = Query(default=0, ge=0),
    limit: int = Query(default=500, ge=1, le=2000),
    level: str | None = Query(default=None),
    search: str | None = Query(default=None),
) -> LogListResponse:
    run = run_svc.get_run(session, run_id)
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")

    entries = log_svc.list_log_entries(
        session,
        run_id,
        after_id=after_id,
        limit=limit,
        level=level,
        search=search,
    )
    return LogListResponse(
        items=[LogEntryItem.from_model(entry) for entry in entries],
        limit=limit,
        after_id=after_id,
    )


def _stream_payload(event: StreamLogEvent | StreamEndEvent) -> str:
    if isinstance(event, StreamLogEvent):
        return json.dumps(
            StreamLogPayload(
                id=event.id,
                run_id=event.run_id,
                ts=event.ts,
                level=event.level,
                logger=event.logger,
                message=event.message,
                context=event.context,
            ).model_dump()
        )
    return json.dumps(StreamEndPayload(status=event.status).model_dump())


async def _stream_run_logs(
    run_id: int,
    *,
    after_id: int,
    terminal_status: str | None,
) -> AsyncIterator[dict[str, str]]:
    seen_ids: set[int] = set()

    entries = await asyncio.to_thread(
        _load_entries_sync,
        run_id,
        after_id,
    )
    for entry in entries:
        if entry.id is None or entry.id in seen_ids:
            continue
        seen_ids.add(entry.id)
        payload = StreamLogPayload(
            id=entry.id,
            run_id=entry.run_id,
            ts=serialize_utc_datetime(entry.ts),
            level=entry.level,
            logger=entry.logger,
            message=entry.message,
            context=entry.context(),
        )
        yield {"event": "message", "data": json.dumps(payload.model_dump())}

    hub = get_log_hub()
    channel = hub.get(run_id)
    if channel is not None:
        for event in channel.backlog(after_id=after_id):
            if event.id in seen_ids:
                continue
            seen_ids.add(event.id)
            yield {"event": "message", "data": _stream_payload(event)}

    if terminal_status is not None:
        end = StreamEndPayload(status=terminal_status)
        yield {"event": "message", "data": json.dumps(end.model_dump())}
        return

    if channel is None or channel.closed:
        status = channel.end_status if channel is not None else "success"
        end = StreamEndPayload(status=status or "success")
        yield {"event": "message", "data": json.dumps(end.model_dump())}
        return

    queue = channel.subscribe()
    try:
        while True:
            live_event: StreamEvent | None = await queue.get()
            if live_event is None:
                break
            if isinstance(live_event, StreamLogEvent):
                if live_event.id in seen_ids:
                    continue
                seen_ids.add(live_event.id)
            yield {"event": "message", "data": _stream_payload(live_event)}
            if live_event.type == "end":
                break
    finally:
        channel.unsubscribe(queue)


def _load_entries_sync(run_id: int, after_id: int) -> list:
    from sqlmodel import Session

    from plextraktbox import db

    with Session(db.engine) as session:
        return log_svc.list_log_entries(session, run_id, after_id=after_id, limit=2000)


@router.get("/{run_id}/logs/stream")
async def stream_run_logs(
    run_id: int,
    _user: CurrentUserDep,
    session: SessionDep,
    after_id: int = Query(default=0, ge=0),
) -> EventSourceResponse:
    run = run_svc.get_run(session, run_id)
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")

    terminal_status = None
    if run.status != JobRunStatus.RUNNING:
        terminal_status = run.status.value

    return EventSourceResponse(
        _stream_run_logs(run_id, after_id=after_id, terminal_status=terminal_status),
        ping=15,
    )
