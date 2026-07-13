# plextraktbox — Architecture

Living design doc for the project — stack, sync engine, data model, and locked decisions (the
"why"). **Phase scope, status, and test plans** live in [phases/README.md](phases/README.md).

## Context

Keep **Plex, Letterboxd, and Trakt** in sync from one self-hosted app with a web UI, replacing the
current approach of stitching two separate projects together:

- [CampAsAChamp/letterboxd-plex-sync](https://github.com/CampAsAChamp/letterboxd-plex-sync) — one-way Letterboxd → Plex (Python; scrapes Letterboxd via `letterboxd_stats`; matches LB URL → TMDB id → Plex guid `tmdb://`).
- [Taxel/PlexTraktSync](https://github.com/Taxel/PlexTraktSync) — two-way Plex ↔ Trakt (Python; `plexapi` + `pytrakt`; **pluggy** plugin sync engine; GUID matching; stateless diffing; `dry_run` everywhere; **no scheduler, no UI**).

Repo and package name: `plextraktbox`.

### Deployment target: TrueNAS

The user will run this on **TrueNAS** (not just any Docker host). Packaging constraints and the
two-milestone deploy plan (personal install → App Catalog) are documented in
[deploy/truenas.md](deploy/truenas.md). Keep container shape compatible from Phase 0 so Phase 12
drops in without rework.



### Locked decisions (from requirements Q&A)

- **Stack:** Python **FastAPI** backend (reuses `plexapi`/`pytrakt` + PlexTraktSync engine patterns) + **React/TypeScript SPA** frontend.
- **Deploy:** **single Docker container** — FastAPI serves the built React bundle + runs an in-process scheduler + SQLite.
- **App auth:** **single local user** (email/username + bcrypt password, session cookie), set in first-run wizard.
- **Letterboxd:** **read-only** (scrape reads; no write-back — Letterboxd has no usable write API for personal use).
- **Jobs:** **per-service-pair jobs**, each independently scheduled/configured.
- **Notifications:** **Discord webhook + in-app**.



### Source-of-truth per data type (drives conflict resolution)

- **Watchlist → Plex is truth.** Reconcile Trakt watchlist to match Plex; LB watchlist read as input only.
- **Ratings → Letterboxd is truth.** Push LB ratings → Plex and Trakt (normalize LB 0.5–5 ↔ Plex/Trakt 0–10).
- **Watched/history → Trakt is truth.** Mark matched items watched in Plex; LB diary read as input only.



## Tech choices

**Backend (Py 3.14+):** FastAPI, uvicorn[standard], SQLModel (+SQLAlchemy), Alembic, **APScheduler** (AsyncIOScheduler + SQLAlchemyJobStore), pydantic-settings, passlib[bcrypt], itsdangerous (Starlette SessionMiddleware), **cryptography Fernet** (encrypt tokens at rest), plexapi, trakt.py, letterboxd_stats + beautifulsoup4/httpx, requests-cache (SQLite HTTP cache), TMDB via httpx, **structlog** (log pipeline), ruff+mypy. Tests: pytest, pytest-asyncio, respx, freezegun.
**Frontend (Node 24+):** React 18 + Vite + TS, TanStack Query, React Router, **Mantine** (admin UI components), `@microsoft/fetch-event-source` (SSE), react-hook-form + zod, `@tanstack/react-virtual` (log virtualization). Tests: Vitest + RTL + MSW.

## Directory structure

```
plextraktbox/
├── Dockerfile (multi-stage: build SPA → copy into python img)  docker-compose.yml  .env.example
├── backend/
│   ├── pyproject.toml  alembic.ini  migrations/
│   └── plextraktbox/
│       ├── main.py (app factory + lifespan: start/stop scheduler)  config.py  db.py
│       ├── security.py (bcrypt, session, Fernet enc/dec)  logging_setup.py
│       ├── models/       user, connection, job, job_run, log_entry, notification, inapp_notification, setting
│       ├── schemas/      wizard, job, run, notification DTOs
│       ├── api/          deps(auth), auth, setup(wizard), connections, jobs, runs, logs_stream(SSE), notifications, health
│       ├── clients/      plex_client, trakt_client, letterboxd_client, tmdb_client (each w/ test_connection())
│       ├── sync/         engine, media_item, guid, matcher, plugins(pluggy), context
│       │   ├── sources/  base(Source ABC), plex_source, trakt_source, letterboxd_source(read-only)
│       │   └── reconcilers/ base, watchlist(Plex-truth), ratings(LB-truth), watched(Trakt-truth)
│       ├── scheduler/    manager(APScheduler lifecycle), runner(execute JobRun + record + notify)
│       ├── notifications/ dispatcher, discord, inapp
│       └── logstream/    pubsub(per-run asyncio pubsub + ring buffer), handler(structlog→DB+pubsub)
│   └── tests/  conftest, fakes/(FakePlex/Trakt/Letterboxd/TMDB), unit/, api/
└── frontend/src/
    ├── App.tsx (router + auth-gate + setup-gate)
    ├── api/ client, jobs, runs, logs(SSE hook), auth
    ├── components/ LogViewer/, JobForm/, layout/(account menu w/ Gravatar avatar)
    └── pages/ SetupWizard/, Login, Dashboard, Jobs, RunHistory, RunDetail(embeds LogViewer), Settings
```



## Sync engine (port PlexTraktSync ideas)

Adapts PlexTraktSync's GUID matching, stateless diffing, dry-run, and **pluggy** engine into **Sources** (per-service read/write adapters) + **Reconcilers** (per-data-type source-of-truth logic).

- `media_item.py` — service-agnostic `MediaItem`: `identifiers{tmdb,imdb,tvdb + native ids}`, `watchlisted`, `rating`, `watched`/`watched_at`, `media_type` (movies first, TV-ready).
- `guid.py` — port of PlexTraktSync `PlexGuid`/`MediaFactory`: parse Plex guids → structured `Guid`; LB path resolves URL → TMDB id → `tmdb://<id>`.
- `matcher.py` — index by identifier priority chain TMDB→IMDb→TVDB; stateless (no persisted mapping).
- **Sources** (`sources/base.py` ABC): `fetch_watchlist/ratings/watched`, `apply_watchlist/ratings/watched(..., dry_run)`, `capabilities`. `PlexSource`/`TraktSource` full read/write; `LetterboxdSource` **read-only** — `apply_`* raise `NotSupported`, capabilities mark writes false (enforces no-write-back at type level).
- **Reconcilers** compute a **plan** then **apply** (skipped on dry_run), each hard-coding its source-of-truth (watchlist=Plex, ratings=Letterboxd, watched=Trakt). Runs only for the sources/data-types a job enables.
- `plugins.py` — pluggy hookspecs (`provide_sources`, `provide_reconcilers`, `before_run`, `after_item`, `after_run`); leaves a seam for future services.
- `engine.run(job, ctx)` — before_run → fetch (cached) → per-data-type reconcile → log every planned change ("would X" on dry-run) → apply with per-item try/except (one failure ≠ abort) → RunSummary (counts: matched/added/removed/rated/watched/skipped/errors).



## Data model (SQLite; secrets Fernet-encrypted at rest)

- **user** — username, email, password_hash(bcrypt); single row enforced in app. Profile image derived from email via [Gravatar](https://gravatar.com) (`avatar_url` on auth responses).
- **connection** — service(plex|trakt|letterboxd|tmdb), status, `config_json`(non-secret: urls/usernames/libraries), `secret_enc`(tokens/password/api key), `token_expires_at`.
- **job** — name, source_pair(e.g. plex_trakt), enabled, cron, dry_run, `require_dry_run_first?`, `data_types_json`(subset of watchlist/ratings/watched), `notify_override_json?`, `exclude_ids_json?`(optional per-job TMDB/IMDb ignore list).
- **job_run** — job_id, trigger(scheduled|manual), dry_run, status(running|success|failed|partial), started/finished_at, `summary_json`, error.
- **log_entry** — run_id(indexed), ts, level, logger, message, `context_json`; index `(run_id,id)` for paging + stream cursor.
- **notification_config** — channel(discord|inapp), enabled, on_success, on_failure, scope(global|job), job_id?, `config_enc`(webhook creds), `config_json`.
- **inapp_notification** — created_at, level, title, body, read, run_id? (powers bell).
- **setting** — key/value_json (default cron, log_retention_days, global dry-run, global exclude/ignore list). Plus APScheduler's `apscheduler_jobs` table in same DB. Retention job prunes old logs/runs.



## Live log streaming (highlighted feature)

Per-run bound structlog logger → custom processor (`logstream/handler.py`) does **(1) persist** `LogEntry` (via async write queue, non-blocking) and **(2) publish** to `logstream/pubsub.py` (process-global `run_id → RunChannel`: per-subscriber `asyncio.Queue` + bounded `deque` ring buffer of last ~500 lines; terminal `{type:end,status}` event on completion).
SSE endpoint `GET /api/runs/{id}/logs/stream` (`EventSourceResponse`): on connect replay historical rows since `?after_id` + ring backlog, then stream live until end. SSE over WS: one-way, proxy-friendly, cookie auth, auto-reconnect.
**React LogViewer:** `fetch-event-source` (reconnect w/ `after_id` cursor, no dupes); **auto-scroll stick-to-bottom** w/ "jump to latest" pill (disengages on manual scroll-up); **timestamp coloring** (muted) + **level prefix colors** (INFO/WARN/ERROR/DEBUG); level filter + text search (server-side level filter for big runs); **virtualized** list for 10k+ lines. Completed runs page historical `LogEntry` via REST through the same component.

## Scheduler + run-now + dry-run

`scheduler/manager.py`: AsyncIOScheduler + SQLAlchemyJobStore, started in FastAPI lifespan; on startup register a CronTrigger per enabled job; job CRUD calls `sync_job()` to add/reschedule/remove live; `max_instances=1`+`coalesce=True` (no self-overlap).
`scheduler/runner.py` is the single entry for **all** executions: create JobRun(running) → bind per-run logger → `engine.run` → finalize (status/summary/error) → close log channel → dispatch notifications.

- **Run now:** `POST /api/jobs/{id}/run` → `scheduler.add_job(next_run_time=now)` so manual + scheduled serialize under `max_instances=1`.
- **Dry-run resolved** per run: `override ?? job.dry_run ?? global`; flows identically through engine (plans + "would…" logs, no `apply_`*).



## Notifications

`notifications/dispatcher.py` called at run finalize: resolve job-override-else-global configs filtered by run status vs on_success/on_failure; build payload from RunSummary (name, status, counts, duration, link `/#/runs/{id}`, error excerpt); fan out concurrently to **discord** (httpx embed, color by status), **inapp** (insert row → bell). Each channel isolated (own try/except; failure logs WARN, never aborts run). `POST /api/notifications/{id}/test` sends synthetic payload.

## Security

- `SECRET_KEY` env (required, validated at startup) derives Fernet key + session signing key; never in DB.
- 3rd-party tokens Fernet-encrypted in `connection.secret_enc`, decrypted only in memory. bcrypt for local password.
- Starlette SessionMiddleware (HttpOnly, SameSite=Lax, Secure over HTTPS); auth dependency gates all routes except `/api/setup/*` (self-disables once a user exists) and `/api/health`; require `X-Requested-With` on mutating requests (CSRF).
- Trakt device OAuth: server-level `TRAKT_CLIENT_ID` / `TRAKT_CLIENT_SECRET` (one API app per deployment); per-user refresh token Fernet-encrypted, auto-refresh on expiry, re-auth in UI on failure.
- structlog redaction processor scrubs token/password-shaped values before persist/stream. Reverse proxy / TLS setup documented in [deploy/truenas.md](deploy/truenas.md) (Phase 12).
- **Planned (Phase 14):** optional [Doppler](https://www.doppler.com/) integration for developer and CI secret injection (`doppler run`, service tokens). Self-hosted TrueNAS installs keep `.env` / app-config as the default — Doppler is for maintainer workflows, not a runtime dependency for end users.



## Phase progress

See [phases/README.md](phases/README.md) for the phase index (status, scope docs, test plans).
**Current focus:** Phase 7 — real Plex/Trakt/Letterboxd **fetch** for movies; apply in Phase 8.



## Verification

- **Phase index:** [phases/README.md](phases/README.md)
- **How to test:** [testing.md](testing.md)
- **Dev ergonomics:** [dev-workflow.md](dev-workflow.md)

When a phase lands: update its scope doc and the table in [phases/README.md](phases/README.md);
copy [phases/test-plans/phase-test-plan-template.md](phases/test-plans/phase-test-plan-template.md)
→ `phases/test-plans/phase-N-test-plan.md`.

### Critical files

- `backend/plextraktbox/sync/engine.py`, `sync/reconcilers/base.py`
- `backend/plextraktbox/scheduler/runner.py`
- `backend/plextraktbox/logstream/pubsub.py`
- `frontend/src/components/LogViewer/`
