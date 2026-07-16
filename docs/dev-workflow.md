# Dev workflow

Day-to-day development setup beyond smoke testing. For container smoke tests and phase checklists,
see [testing.md](testing.md).

## Prerequisites

```bash
mise trust && mise install   # first clone only
mise run install             # backend venv + frontend deps + git hooks
```

### Corporate TLS (Zscaler)

On a Zscaler (or similar) laptop, native `mise run install` / `dev-*` usually use the **host** trust
store. For **prod** image builds on that laptop, set `USE_CORPORATE_CA=1` in `.env` so `npm`/`pip`
inside the Dockerfile trust [`docker/certs/`](../docker/certs/). The CA is used at build time only
and is **not** present in the published GHCR / TrueNAS runtime image. Dev compose images
(`Dockerfile.dev-*`) still include the CA for local hot-reload Docker. Details:
[docker/certs/README.md](../docker/certs/README.md).

`mise run install` sets `git config core.hooksPath .githooks` so:

- **commit-msg** — subjects must be [Conventional Commits](https://www.conventionalcommits.org/)
  (needed for semantic-release)
- **pre-push** — runs `mise run check` (lint + typecheck + tests) before `git push`

If you skip that task: `git config core.hooksPath .githooks`. Emergency bypass:
`git push --no-verify`.

Run `mise tasks` for the full task list.

## Lint and format

`mise run lint` (and thus `mise run check` / pre-push) covers:

- **Backend:** Ruff lint + format check (including import sorting via Ruff `I`) and mypy
- **Frontend:** ESLint (`npm run lint`), Prettier check (`npm run format:check`), and TypeScript (`npm run typecheck`)

Frontend helpers from `frontend/`:

```bash
npm run lint          # ESLint (absolute src/ imports + import sort + hooks)
npm run lint:fix     # autofix import order / safe fixes
npm run format        # Prettier write
npm run format:check  # Prettier CI check
```

## Doppler (maintainers — recommended)

[Doppler](https://www.doppler.com/) holds **maintainer** bootstrap secrets. Local `.env` keeps only
non-secret knobs (`DATA_DIR`, `SYNC_RUN_DELAY_SECONDS`, …). Self-hosted / TrueNAS installs ignore
Doppler and use `.env` or the app-config UI.

**What belongs in Doppler** (project `plextraktbox`, configs `local` / `ci`):

- Required: `SECRET_KEY`, `TRAKT_CLIENT_ID`, `TRAKT_CLIENT_SECRET`
- Optional for `dev-bootstrap`: `DEV_*`, `PLEX_*`, `TMDB_API_KEY`, `LETTERBOXD_*`, Trakt user tokens

**One-time setup:**

1. Create the Doppler project/configs and paste secrets in the Doppler dashboard.
2. Install the [Doppler CLI](https://docs.doppler.com/docs/install-cli), then:

```bash
doppler login
doppler setup   # reads doppler.yaml → project plextraktbox, config local
```

**Day-to-day:**

```bash
mise run up-dev          # hot-reload stack, secrets from Doppler (default)
mise run up-doppler      # prod container, secrets from Doppler
mise run check-doppler   # lint + tests with Doppler-injected env
mise run down-dev
```

Without Doppler, use `mise run up-dev-env` and put secrets in `.env` (see
[`.env.example`](../.env.example)).

GitHub Actions still stubs a dummy `.env` for the default `check` job (no Doppler required). To
run optional live-credential CI later, add a Doppler service token as `DOPPLER_TOKEN` and wrap
those steps with `doppler run --` against the `ci` config.

## Local dev (hot reload)

Pick one approach — do **not** run `up` and `up-dev` together (both bind the HTTP listen port,
default 8000; set `PORT` in `.env` to change it for prod compose).

**One terminal (container dev — recommended for maintainers):**

```bash
mise run up-dev      # Doppler + backend :8000 + Vite :5173
mise run rebuild-dev # no-cache image rebuild after dependency changes (also uses Doppler)
mise run down-dev
```

`up-dev` runs a wrapper around `doppler run -- compose up --build` that rebuilds when Dockerfiles or
dependency files change, and on Ctrl+C waits for `compose down` to finish so shutdown logs do not
spill into the next prompt. After changing `pyproject.toml` or `package.json`, use
`mise run rebuild-dev`. Source edits under `backend/` and `frontend/` reload live via bind mounts.

**Two terminals (native, no Docker):**

```bash
doppler run -- mise run dev-backend    # terminal 1 — uvicorn on :8000
mise run dev-frontend                  # terminal 2 — Vite on :5173
```

Native dev and docker both use `./data` at the repo root (`DATA_DIR` in `.env`). Open the Vite URL
(usually http://localhost:5173); both processes must be running for the health badge to go green.

## API smoke sessions

Authenticated curl examples use a cookie jar (`cookies.txt`). Create it once per dev session:

```bash
mise run api-login
# uses DEV_USER/DEV_PASSWORD from Doppler (or prompts); writes cookies.txt
```

Use the saved jar on later curls:

```bash
curl -s -b cookies.txt http://localhost:8000/api/jobs
```

## Dev bootstrap (after wiping `./data`)

After `mise run down-v` or `mise run clean-data`, skip the setup wizard by seeding from Doppler (or
a filled `.env` if not using Doppler):

1. **Once**, after configuring connections in the UI, capture secrets into Doppler (or `.env`):

   ```bash
   mise run dev-export-secrets   # review output; paste into Doppler `local` (set DEV_PASSWORD in Doppler too)
   ```

   Export reads `DATA_DIR` from `.env` (use `./data` for docker dev). It logs which database file
   it opened. If you previously ran docker when mise forced `SECRET_KEY=dev`, run
   `mise run dev-reencrypt-secrets` once so tokens match your current key, then export again.

2. Ensure `DEV_USER`, `DEV_PASSWORD`, and any connection vars you need are in Doppler `local`.

3. Start the app, then bootstrap:

   ```bash
   mise run up-dev          # or: doppler run -- mise run dev-backend
   mise run dev-bootstrap   # creates user, logs in, saves connections, writes cookies.txt
   ```

Use `mise run dev-bootstrap -- --force` to re-save connections even when they already show `ok`.
Use `mise run dev-bootstrap -- --wait 60` if the API is slow to start.
