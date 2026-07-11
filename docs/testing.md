# Testing guide

How to verify each project phase. Shared setup lives here; per-phase checklists live in
`docs/phase-N-test-plan.md` files linked from [PLAN.md](../PLAN.md#phase-tracker).

## Prerequisites

```bash
mise trust && mise install   # first clone only
mise run install             # backend venv + frontend deps
```

Run `mise tasks` for the full task list.

## Shared setup (container)

The container serves **both** the API and the built React app on port 8000. You do not need a
separate Vite dev server for smoke testing.

```bash
# First time only (skip if you already have .env from Phase 0):
# cp .env.example .env && set SECRET_KEY and Trakt API app credentials

mise run up   # or: podman compose up --build
```

Open **http://localhost:8000**.

```bash
mise run down      # stop, keep ./data
mise run down-v    # stop and wipe ./data (fresh DB / first-run wizard)
mise run rebuild   # down-v + build + up
```

## Automated checks (every phase)

```bash
mise run test      # pytest + vitest
mise run check     # lint, typecheck, and tests (CI parity)
```

## Phase test plans

| Phase | Scope | Test plan | Status |
| ----- | ----- | --------- | ------ |
| 0 | Scaffold, health, SPA shell | [phase-0-test-plan.md](phase-0-test-plan.md) | Done |
| 1 | Auth, sessions, setup wizard | [phase-1-test-plan.md](phase-1-test-plan.md) | Done |
| 2 | Connections + wizard steps | [phase-2-test-plan.md](phase-2-test-plan.md) | Done |
| 3 | Sync engine core + dry-run | [phase-3-test-plan.md](phase-3-test-plan.md) | Done |
| 4 | Jobs, runs, scheduler | [phase-4-test-plan.md](phase-4-test-plan.md) | Done |
| 5 | Logging pipeline + live viewer | [phase-5-test-plan.md](phase-5-test-plan.md) | Done |
| 6 | Notifications | [phase-6-test-plan.md](phase-6-test-plan.md) | Done |
| 7 | Client-backed sources (movies) | [phase-7-test-plan.md](phase-7-test-plan.md) | Next |
| 8 | Settings, safety & operations | — | TBD when phase lands |
| 9 | Dashboard & scheduling UX | — | TBD when phase lands |
| 10 | TV sync (shows + episodes) | — | TBD when phase lands |
| 11 | TrueNAS personal install | — | TBD when phase lands |
| 12 | TrueNAS App Catalog | — | TBD when phase lands |
| 13 | Doppler secret management (dev/CI) | — | TBD when phase lands |
| 14 | UI polish & layout rework | — | TBD when phase lands |

When a phase is implemented, copy [phase-test-plan-template.md](phase-test-plan-template.md),
fill in the checklist, add a row link above, and link it from the phase line in PLAN.md.

## Local dev (hot reload)

For **day-to-day development** with hot reload, use either:

**One terminal (container dev):**

```bash
mise run up-dev     # backend :8000 + Vite :5173, bind-mounted source
mise run rebuild-dev # no-cache image rebuild after dependency changes
mise run down-dev
```

**Two terminals (native, no Docker):**

```bash
mise run dev-backend    # terminal 1 — uvicorn on :8000
mise run dev-frontend   # terminal 2 — Vite on :5173
```

See [phase-0-test-plan.md](phase-0-test-plan.md) §2 for details. Open the Vite URL (usually
http://localhost:5173); both processes must be running for the health badge to go green. Do not
run `up` and `up-dev` together — both use port 8000.

## API smoke sessions

Authenticated curl examples in phase test plans use a cookie jar (`cookies.txt`). Create it once
per dev session:

```bash
mise run api-login
# prompts for username/password (hidden), writes cookies.txt, verifies /api/auth/me
```

To skip prompts, add to your gitignored `.env` (see `.env.example`):

```bash
DEV_USER=nick
DEV_PASSWORD=your-password
```

Then `mise run api-login` reads those vars automatically. Use the saved jar on later curls:

```bash
curl -s -b cookies.txt http://localhost:8000/api/jobs
```

## Dev bootstrap (after wiping `./data`)

After `mise run down-v`, `mise run clean-data`, or `mise run rebuild`, skip the setup wizard by
seeding from your gitignored `.env`:

1. **Once**, after configuring connections in the UI, capture secrets into `.env`:

   ```bash
   mise run dev-export-secrets >> .env   # review before saving; password must be set manually
   ```

   Export reads `DATA_DIR` from `.env` (use `./data` for docker dev). It logs which database
   file it opened. If you previously ran docker when mise forced `SECRET_KEY=dev`, run
   `mise run dev-reencrypt-secrets` once so tokens match your `.env` key, then export again.

2. Ensure `DEV_USER`, `DEV_PASSWORD`, and any connection vars you need
   are in `.env` (see `.env.example`).

3. Start the app, then bootstrap:

   ```bash
   mise run up-dev          # or dev-backend / up
   mise run dev-bootstrap   # creates user, logs in, saves connections, writes cookies.txt
   ```

Use `mise run dev-bootstrap -- --force` to re-save connections even when they already show `ok`.
Use `mise run dev-bootstrap -- --wait 60` if the API is slow to start.
