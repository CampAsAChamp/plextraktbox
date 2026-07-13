# plextraktbox — agent guide

Self-hosted app that keeps **Plex**, **Letterboxd**, and **Trakt** in sync — web UI, scheduler, live log streaming, notifications. Single Docker container (FastAPI + React SPA + SQLite + APScheduler).

**Design doc:** [docs/PLAN.md](docs/PLAN.md) (architecture, locked decisions — keep in sync when behavior changes).
**Phase roadmap:** [docs/phases/](docs/phases/) (scope per phase) + [docs/PLAN.md#phase-tracker](docs/PLAN.md#phase-tracker) (status).
**Human docs:** [README.md](README.md), [docs/testing.md](docs/testing.md).

## Sync model (source of truth)

| Data type | Source of truth | Notes |
| --------- | --------------- | ----- |
| Watchlist | **Plex** | Reconcile Trakt to Plex; Letterboxd read-only |
| Ratings | **Letterboxd** | Push LB → Plex and Trakt (0.5–5 ↔ 0–10) |
| Watched | **Trakt** | Mark matched items watched in Plex; LB read-only |

Letterboxd has **no write API** — `LetterboxdSource.apply_*` must stay unsupported.

## Stack

- **Backend:** Python 3.14, FastAPI, SQLModel, Alembic, APScheduler, structlog, plexapi, trakt.py, letterboxd_stats
- **Frontend:** React 18, TypeScript, Vite, Mantine, TanStack Query, react-hook-form + zod
- **Tooling:** [mise.toml](mise.toml) pins Python/Node and defines all dev tasks
- **Deploy target:** TrueNAS SCALE (single container, `/data` ZFS mount, port 8000)

## Layout

```
backend/plextraktbox/
  api/           REST routes (auth, setup, connections, jobs, runs, logs SSE)
  clients/       Plex, Trakt, Letterboxd, TMDB HTTP adapters
  sync/          engine, sources, reconcilers, guid, matcher, plugins (pluggy)
  models/        SQLModel tables
  services/      business logic (jobs, sync_run, source_factory)
frontend/src/    React SPA (setup wizard, connections, jobs, run history)
docs/            phase test plans + testing guide
```

## Commands

Task groups are shown in `mise tasks` descriptions as `[META]`, `[LOCAL]`, `[DOCKER-PROD]` (production container), and `[DOCKER-DEV]` (dev containers with hot reload).

```bash
mise trust && mise install   # first clone — installs tool versions only
mise run install             # backend venv + frontend deps
mise run dev-backend         # uvicorn :8000 (terminal 1)
mise run dev-frontend        # Vite :5173 (terminal 2)
mise run up-dev              # container dev with hot reload
mise run test                # pytest + vitest
mise run check               # lint + typecheck + tests (CI parity)
mise run db-upgrade          # apply Alembic migrations
mise run up                  # production container on :8000
```

Do not run `up` and `up-dev` simultaneously — both bind port 8000.

## Git

Personal repo — plain imperative commit subjects, no trailing period (no conventional commits unless asked). Match recent `git log`. Only commit when the user asks.

## Coding principles

1. **Minimize scope** — smallest correct diff; no drive-by refactors.
2. **Match existing patterns** — read surrounding code before adding.
3. **Dry-run everywhere** — sync engine must support dry-run with "would …" logs and zero writes.
4. **Per-item fault isolation** — one failed apply must not abort the whole run.
5. **Secrets** — never commit `.env`; tokens Fernet-encrypted in DB; structlog redacts sensitive values.
6. **Tests** — add meaningful tests for behavior changes; run `mise run check` before finishing.

## Sync engine conventions

- **Sources** (`sync/sources/`): read/write adapters per service; Letterboxd is read-only.
- **Reconcilers** (`sync/reconcilers/`): one per data type; hard-code source-of-truth rules.
- **Engine** (`sync/engine.py`): fetch → plan → log → apply; returns `RunSummary`.
- **Matching** (`sync/guid.py`, `sync/matcher.py`): TMDB → IMDb → TVDB priority; stateless (no persisted mapping).
- **Fakes** for tests live in `backend/tests/fakes/`.

## Phase progress

See [docs/PLAN.md#phase-tracker](docs/PLAN.md#phase-tracker) and [docs/phases/](docs/phases/). Phases 0–6 are done; **Phase 7 (client-backed sources, movies)** is next, followed by settings/safety (8), dashboard UX (9), and TV sync (10). Visual/layout polish is intentionally deferred to **Phase 14** — earlier phases prioritize working features.

When a phase lands, update its doc under `docs/phases/`, add/update its test plan under
`docs/phases/test-plans/`, and link from `docs/PLAN.md`.

## Keeping this file current

Update **CLAUDE.md** and `.cursor/rules/` / `.claude/rules/` in the same PR when you change stack, commands, sync rules, or phase status. Prefer brief, verified facts over exhaustive file lists.
