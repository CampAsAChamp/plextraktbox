# Testing guide

How to verify the project and each development phase.

- **Phase index** (scope + checklists): [phases/README.md](phases/README.md)
- **Day-to-day dev** (hot reload, bootstrap): [dev-workflow.md](dev-workflow.md)

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

Or run each stack separately:

```bash
mise run test-backend
mise run test-frontend
```

GitHub Actions (`.github/workflows/ci.yml`) runs `mise run check` on pull requests and
pushes to `main`. The workflow stubs a CI `.env` (dummy `SECRET_KEY` / Trakt placeholders);
pytest uses in-process FastAPI + throwaway SQLite — not a live container. Doppler is optional for
maintainers (`mise run check-doppler`); default CI does not require a Doppler token.

## Phase verification

Per-phase checklists live in [phases/test-plans/](phases/test-plans/). The master index is
[phases/README.md](phases/README.md) — update that table when a phase lands.

When implementing a new phase: copy
[phases/test-plans/phase-test-plan-template.md](phases/test-plans/phase-test-plan-template.md) →
`phases/test-plans/phase-N-test-plan.md` and add a row to [phases/README.md](phases/README.md).

## Testing conventions

Reference for phase test plans and automated tests:

- **Container (default):** `mise run up` → http://localhost:8000
- **Local dev (hot reload):** see [dev-workflow.md](dev-workflow.md)
- **Automated:** `mise run test` / `mise run check` (same bar as GitHub Actions CI)
- **Sync engine (Phase 3+):** fakes in `tests/fakes/` via `SyncContext` (no network); assert
  source-of-truth per data type; dry-run = zero writes
- **HTTP/time:** `respx`, `freezegun`
- **API:** httpx AsyncClient + in-memory SQLite
- **Frontend:** vitest + RTL (+ MSW where needed)
- **Client-backed fetch (Phase 7):** unit tests on fakes; respx for HTTP mapping; optional manual dry-run with real creds
- **Client-backed apply (Phase 8):** respx for apply payloads; cautious manual live-run verification
- **Settings / ops (Phase 13):** settings CRUD + backup; dry-run first coerce; exclude filter; retention;
  connection health transition notify; health `ok`/`degraded`
- **Dashboard / scheduling UX (Phase 14):** `last_run` on jobs; clone job; log export txt/jsonl; cron
  presets; dashboard ops actions
- **Doppler (Phase 15):** `mise run up-dev` (default hot reload) / `up-doppler` / `check-doppler`;
  optional CI `DOPPLER_TOKEN` — secrets in Doppler, knobs in `.env` (see [dev-workflow.md](dev-workflow.md))
- **TrueNAS (Phases 22–23):** real hardware / catalog install — see [deploy/truenas.md](deploy/truenas.md) and phase test plans
