# Phase 0 — Scaffold

**Status:** Done

## Goal

Establish the project skeleton so a single container boots, serves a health endpoint, loads the SPA
shell, and persists data on a `/data` volume — the foundation every later phase builds on.

## Deliverables

- Monorepo layout: `backend/`, `frontend/`, root Docker/compose files
- Python project (`pyproject.toml`), FastAPI app factory, pydantic-settings config
- SQLite + SQLModel + Alembic baseline migration
- Multi-stage **Dockerfile** (build Vite SPA → copy into Python runtime image)
- **docker-compose.yml** with `/data` volume mount and `.env.example`
- `GET /api/health` returning status + version
- Minimal React/Vite SPA shell with health badge (live version via `/api/health` — see [Phase 18](phase-18.md))
- `mise.toml` tasks for install, dev, container workflows

## Key files

- `Dockerfile`, `docker-compose.yml`, `.env.example`
- `backend/plextraktbox/main.py`, `config.py`, `db.py`
- `frontend/src/App.tsx`
- `mise.toml`

## Prerequisites

None — first phase.

## Defers to later phases

- Auth, connections, sync engine, scheduler, logging, notifications (Phases 1–6)
- TrueNAS-specific packaging kept in mind but not implemented yet

## Verification

[phase-0-test-plan.md](test-plans/phase-0-test-plan.md) — container boot, health OK, SPA loads (container +
Vite dev + backend static).

## Historical note — package rename

Between Phase 0 and Phase 1, the project was renamed from `media-sync` to **plextraktbox** (Python
package, env prefix, Docker/CI/docs). No separate test plan — covered by Phase 0 smoke tests.

**Next:** [Phase 1 — Auth + wizard](phase-1.md)
