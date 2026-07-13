# Phase 5 — Logging pipeline + live viewer

**Status:** Done

## Goal

Structured per-run logs persisted to SQLite and streamed live over SSE, with a polished React
LogViewer for both in-progress and completed runs.

## Deliverables

- **structlog** pipeline with per-run bound logger
- **logstream/handler.py** — async write queue → `log_entry` table + pub/sub publish
- **logstream/pubsub.py** — `run_id → RunChannel` with subscriber queues + ~500-line ring buffer;
  terminal `{type:end,status}` event
- REST: `GET /api/runs/{id}/logs` (paging, level filter, search)
- SSE: `GET /api/runs/{id}/logs/stream` — replay since `?after_id` + live until end
- **LogViewer** component:
  - `fetch-event-source` with reconnect + `after_id` cursor (no duplicates)
  - Auto-scroll stick-to-bottom + "jump to latest" pill
  - Timestamp + level coloring; level filter + text search
  - Virtualized list (`@tanstack/react-virtual`) for 10k+ lines
- Run detail embeds LogViewer (live + historical modes)

## Key files

- `backend/plextraktbox/logstream/`, `api/logs_stream.py`, `models/log_entry.py`
- `frontend/src/components/LogViewer/`

## Prerequisites

[Phase 4](phase-4.md)

## Defers to later phases

- Log export download (Phase 10)
- Log retention pruning job (Phase 9)

## Verification

[phase-5-test-plan.md](test-plans/phase-5-test-plan.md)

**Next:** [Phase 6 — Notifications](phase-6.md)
