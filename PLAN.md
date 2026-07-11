# plextraktbox — Plan & Progress Tracker

This is the living design doc and phase tracker for the project. Check items off as phases land;
update the design sections in place as decisions evolve (don't let this go stale — it's the source of
truth for "why," not just "what").

## Context

Keep **Plex, Letterboxd, and Trakt** in sync from one self-hosted app with a web UI, replacing the
current approach of stitching two separate projects together:

- [CampAsAChamp/letterboxd-plex-sync](https://github.com/CampAsAChamp/letterboxd-plex-sync) — one-way Letterboxd → Plex (Python; scrapes Letterboxd via `letterboxd_stats`; matches LB URL → TMDB id → Plex guid `tmdb://`).
- [Taxel/PlexTraktSync](https://github.com/Taxel/PlexTraktSync) — two-way Plex ↔ Trakt (Python; `plexapi` + `pytrakt`; **pluggy** plugin sync engine; GUID matching; stateless diffing; `dry_run` everywhere; **no scheduler, no UI**).

Repo and package name: `plextraktbox`.

### Deployment target: TrueNAS

The user will run this on **TrueNAS** (not just any Docker host) — this shapes packaging/ops decisions:

- Ship as a container TrueNAS can run via its **Apps** system (TrueNAS SCALE uses a Kubernetes-backed
custom app / "Launch Docker Image" workflow, or a catalog app if published later). Keep the image
self-contained (single container, SQLite, `/data` volume) since that maps directly onto TrueNAS's
"custom app" model (image + port + host-path volume mount).
- Avoid host-network assumptions and hardcoded UIDs — TrueNAS apps commonly run rootless/with
configurable PUID/PGID for permissions on the mounted dataset. Prefer standard `PUID`/`PGID`-style env
vars so file ownership on the ZFS dataset behaves.
- `/data` should map to a TrueNAS dataset (ZFS), not a Docker-managed volume, when deployed there.
- No dependency on host Docker socket, no privileged mode, no macvlan networking — a plain container
exposing one HTTP port is the easiest shape to drop into TrueNAS's app UI.
- Not a Phase 0 concern, but keep these constraints in mind whenever touching
Dockerfile/compose/entrypoint so there's no retrofit later.

**Two distinct milestones, in order — don't conflate them:**

1. **Phase 8 (personal install):** run the built image on the user's own TrueNAS box via the custom-app /
  "Launch Docker Image" flow. No catalog involvement — just a working container + dataset mount on one
   machine. This is the near-term goal.
2. **Phase 9 (catalog publication):** get `plextraktbox` actually listed in the **TrueNAS App Catalog** so
  it can be installed like any official/community app. A separate, heavier lift:
  - Package the app per TrueNAS SCALE's current app spec (a chart/`app.yaml`-style app definition with a
  config schema) rather than just a raw Docker image — check the current SCALE app format when this
  phase starts, since it has changed across releases.
  - Define the schema for user-configurable options (port, `/data` dataset path,
  `SECRET_KEY`, etc.) through TrueNAS's app config UI, not just env vars in a compose file.
  - Publish the container image to a public registry (e.g. GHCR) with versioned tags — a catalog entry
  can't point at a local-only image.
  - Submit to (or stand up) a TrueNAS apps catalog/train — either the official community catalog (via
  their contribution process) or a self-hosted custom catalog added by URL; confirm the current
  submission process/requirements at the time, since catalog mechanics are a moving target.
  - Go through whatever review/validation TrueNAS requires before the app is listed and installable from
  the catalog UI.
  - Only start once Phase 8 has been running successfully for a while — publishing before the app is
  proven on real hardware is premature.



### Locked decisions (from requirements Q&A)

- **Stack:** Python **FastAPI** backend (reuses `plexapi`/`pytrakt` + PlexTraktSync engine patterns) + **React/TypeScript SPA** frontend.
- **Deploy:** **single Docker container** — FastAPI serves the built React bundle + runs an in-process scheduler + SQLite.
- **App auth:** **single local user** (email/username + bcrypt password, session cookie), set in first-run wizard.
- **Letterboxd:** **read-only** (scrape reads; no write-back — Letterboxd has no usable write API for personal use).
- **Jobs:** **per-service-pair jobs**, each independently scheduled/configured.
- **Notifications:** **Discord webhook + Email (SMTP) + in-app**.



### Source-of-truth per data type (drives conflict resolution)

- **Watchlist → Plex is truth.** Reconcile Trakt watchlist to match Plex; LB watchlist read as input only.
- **Ratings → Letterboxd is truth.** Push LB ratings → Plex and Trakt (normalize LB 0.5–5 ↔ Plex/Trakt 0–10).
- **Watched/history → Trakt is truth.** Mark matched items watched in Plex; LB diary read as input only.



## Tech choices

**Backend (Py 3.11+):** FastAPI, uvicorn[standard], SQLModel (+SQLAlchemy), Alembic, **APScheduler** (AsyncIOScheduler + SQLAlchemyJobStore), pydantic-settings, passlib[bcrypt], itsdangerous (Starlette SessionMiddleware), **cryptography Fernet** (encrypt tokens at rest), plexapi, trakt.py, letterboxd_stats + beautifulsoup4/httpx, requests-cache (SQLite HTTP cache), TMDB via httpx, **structlog** (log pipeline), aiosmtplib (email), ruff+mypy. Tests: pytest, pytest-asyncio, respx, freezegun.
**Frontend (Node 20+):** React 18 + Vite + TS, TanStack Query, React Router, **Mantine** (admin UI components), `@microsoft/fetch-event-source` (SSE), react-hook-form + zod, `@tanstack/react-virtual` (log virtualization). Tests: Vitest + RTL + MSW.

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
│       ├── notifications/ dispatcher, discord, email, inapp
│       └── logstream/    pubsub(per-run asyncio pubsub + ring buffer), handler(structlog→DB+pubsub)
│   └── tests/  conftest, fakes/(FakePlex/Trakt/Letterboxd/TMDB), unit/, api/
└── frontend/src/
    ├── App.tsx (router + auth-gate + setup-gate)
    ├── api/ client, jobs, runs, logs(SSE hook), auth
    ├── components/ LogViewer/, JobForm/, layout/
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

- **user** — username, email, password_hash(bcrypt); single row enforced in app.
- **connection** — service(plex|trakt|letterboxd|tmdb), status, `config_json`(non-secret: urls/usernames/libraries), `secret_enc`(tokens/password/api key), `token_expires_at`.
- **job** — name, source_pair(e.g. plex_trakt), enabled, cron, dry_run, `data_types_json`(subset of watchlist/ratings/watched), `notify_override_json?`.
- **job_run** — job_id, trigger(scheduled|manual), dry_run, status(running|success|failed|partial), started/finished_at, `summary_json`, error.
- **log_entry** — run_id(indexed), ts, level, logger, message, `context_json`; index `(run_id,id)` for paging + stream cursor.
- **notification_config** — channel(discord|email|inapp), enabled, on_success, on_failure, scope(global|job), job_id?, `config_enc`(webhook/SMTP creds), `config_json`.
- **inapp_notification** — created_at, level, title, body, read, run_id? (powers bell).
- **setting** — key/value_json (default cron, log_retention_days, global dry-run). Plus APScheduler's `apscheduler_jobs` table in same DB. Retention job prunes old logs/runs.



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

`notifications/dispatcher.py` called at run finalize: resolve job-override-else-global configs filtered by run status vs on_success/on_failure; build payload from RunSummary (name, status, counts, duration, link `/#/runs/{id}`, error excerpt); fan out concurrently to **discord** (httpx embed, color by status), **email** (aiosmtplib HTML+text), **inapp** (insert row → bell). Each channel isolated (own try/except; failure logs WARN, never aborts run). `POST /api/notifications/{id}/test` sends synthetic payload.

## Security

- `SECRET_KEY` env (required, validated at startup) derives Fernet key + session signing key; never in DB.
- 3rd-party tokens Fernet-encrypted in `connection.secret_enc`, decrypted only in memory. bcrypt for local password.
- Starlette SessionMiddleware (HttpOnly, SameSite=Lax, Secure over HTTPS); auth dependency gates all routes except `/api/setup/*` (self-disables once a user exists) and `/api/health`; require `X-Requested-With` on mutating requests (CSRF).
- Trakt device OAuth: server-level `TRAKT_CLIENT_ID` / `TRAKT_CLIENT_SECRET` (one API app per deployment); per-user refresh token Fernet-encrypted, auto-refresh on expiry, re-auth in UI on failure.
- structlog redaction processor scrubs token/password-shaped values before persist/stream. Document running behind a reverse proxy for TLS.
- **Planned (Phase 10):** optional [Doppler](https://www.doppler.com/) integration for developer and CI secret injection (`doppler run`, service tokens). Self-hosted TrueNAS installs keep `.env` / app-config as the default — Doppler is for maintainer workflows, not a runtime dependency for end users.



## Phase tracker

Each phase is independently runnable/testable. Check off as completed.

- [x] **Phase 0 — Scaffold** — layout, pyproject, Vite, multi-stage Dockerfile, compose w/ `/data` volume, config+DB+Alembic baseline, `/api/health`. *Verified: container boots, health OK, SPA loads (container + Vite dev + backend static).* → [test plan](docs/phase-0-test-plan.md)
- [x] **Rename** — `media-sync` package → `plextraktbox` (package, env prefix, Docker/CI/docs).
- [x] **Phase 1 — Auth + wizard (user)** — user model, bcrypt, sessions, auth dep, `setup/user`+`login`/`logout`, SPA setup-gate→login→dashboard. → [test plan](docs/phase-1-test-plan.md)
- [x] **Phase 2 — Connections + wizard steps** — connection model + Fernet, four clients w/ `test_connection()`, Plex PIN auth + Trakt device + LB creds + TMDB key steps, re-auth UI. → [test plan](docs/phase-2-test-plan.md)
- [x] **Phase 3 — Sync engine core** — MediaItem/guid/matcher/plugins/sources/3 reconcilers/engine + dry-run; temporary synchronous `POST /api/jobs/{id}/run`. *Full unit coverage of matching + each source-of-truth reconciler vs fakes; dry-run = zero writes.* → [test plan](docs/phase-3-test-plan.md)
- [ ] **Phase 4 — Jobs + runs + scheduler** — Job/JobRun models, jobs CRUD API + JobForm UI, APScheduler manager+runner, run history list/detail. *(test plan: TBD)*
- [ ] **Phase 5 — Logging pipeline + live viewer** — structlog config, DB+pubsub handler, ring buffer, SSE endpoint, LogViewer (auto-scroll/colors/filter/virtualization), live + historical modes. *(test plan: TBD)*
- [ ] **Phase 6 — Notifications** — config model + CRUD UI, dispatcher, discord/email/inapp, per-job override + global, test buttons, in-app bell. *(test plan: TBD)*
- [ ] **Phase 7 — Hardening** — retention job, redaction, error surfaces, OpenAPI→TS types, README, e2e smoke, **GitHub Actions CI** (restore `.github/workflows/ci.yml`: backend ruff/mypy/pytest, frontend typecheck/vitest/build; fix current failures; mirror `mise run check`), polish. *(test plan: TBD)*
- [ ] **Phase 8 — TrueNAS deployment (personal install)** — confirm `PUID`/`PGID`-style permission handling against a ZFS dataset mount, document the "Launch Docker Image" / custom-app setup in the README, do a real install on the user's TrueNAS box end to end (wizard → jobs → scheduled run → notification). *(test plan: TBD)*
- [ ] **Phase 9 — TrueNAS App Catalog publication** — package per current TrueNAS SCALE app spec, publish image to a public registry with versioned tags, submit to / stand up a catalog, get through review, verify catalog install. Only start once Phase 8 has run successfully for a while. *(test plan: TBD)*
- [ ] **Phase 10 — Doppler secret management** — integrate [Doppler](https://www.doppler.com/) for maintainer dev/CI workflows while keeping `.env` as the self-hosted default. Scope: create Doppler project + `dev`/`ci` configs mapping existing env vars (`SECRET_KEY`, `TRAKT_CLIENT_ID`, `TRAKT_CLIENT_SECRET`, etc.); add `doppler.yaml`; document `doppler setup` + `doppler run` for local dev and `mise run up`; optional `doppler run --` wrapper tasks in `mise.toml`; CI service-token injection for integration tests that need real creds; entrypoint/compose notes for optional production injection. Verify: fresh clone with Doppler CLI can boot container and pass `mise run check` without a hand-edited `.env`. *(test plan: TBD)*



## Verification

Per-phase checklists live in `docs/phase-N-test-plan.md`. Start at [docs/testing.md](docs/testing.md) for
shared setup (`mise run up`, `mise run test`, reset commands) and the phase index.

When a phase lands: copy [docs/phase-test-plan-template.md](docs/phase-test-plan-template.md) →
`docs/phase-N-test-plan.md`, fill in automated + manual checks, link it from the phase tracker above
and the table in `testing.md`.

**Testing conventions (reference for future phase docs):**

- **Container (default):** `mise run up` → http://localhost:8000
- **Local dev (hot reload):** `mise run dev-backend` + `mise run dev-frontend` (two terminals)
- **Automated:** `mise run test` / `mise run check` (local CI parity until GitHub Actions is restored in Phase 7)
- **Sync engine (Phase 3+):** fakes in `tests/fakes/` via `SyncContext` (no network); assert
  source-of-truth per data type; dry-run = zero writes
- **HTTP/time:** `respx`, `freezegun`
- **API:** httpx AsyncClient + in-memory SQLite
- **Frontend:** vitest + RTL (+ MSW where needed)
- **TrueNAS (Phases 8–9):** real hardware / catalog install — documented in those phase test plans
- **Doppler (Phase 10):** `doppler run` boot + CI token injection — no committed `.env` required for maintainers



### Critical files

- `backend/plextraktbox/sync/engine.py`, `sync/reconcilers/base.py`
- `backend/plextraktbox/scheduler/runner.py`
- `backend/plextraktbox/logstream/pubsub.py`
- `frontend/src/components/LogViewer/`

