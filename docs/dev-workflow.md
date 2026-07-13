# Dev workflow

Day-to-day development setup beyond smoke testing. For container smoke tests and phase checklists,
see [testing.md](testing.md).

## Prerequisites

```bash
mise trust && mise install   # first clone only
mise run install             # backend venv + frontend deps
```

Run `mise tasks` for the full task list.

## Local dev (hot reload)

Pick one approach — do **not** run `up` and `up-dev` together (both bind port 8000).

**One terminal (container dev):**

```bash
mise run up-dev      # backend :8000 + Vite :5173, bind-mounted source
mise run rebuild-dev # no-cache image rebuild after dependency changes
mise run down-dev
```

`up-dev` runs `compose up --build`, which rebuilds when Dockerfiles or dependency files change.
After changing `pyproject.toml` or `package.json`, use `mise run rebuild-dev`. Source edits under
`backend/` and `frontend/` reload live via bind mounts.

**Two terminals (native, no Docker):**

```bash
mise run dev-backend    # terminal 1 — uvicorn on :8000
mise run dev-frontend   # terminal 2 — Vite on :5173
```

Native dev and docker both use `./data` at the repo root (`DATA_DIR` in `.env`). Open the Vite URL
(usually http://localhost:5173); both processes must be running for the health badge to go green.

See [phases/test-plans/phase-0-test-plan.md](phases/test-plans/phase-0-test-plan.md) §2 for
container vs native smoke details.

## API smoke sessions

Authenticated curl examples in phase test plans use a cookie jar (`cookies.txt`). Create it once per
dev session:

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

   Export reads `DATA_DIR` from `.env` (use `./data` for docker dev). It logs which database file
   it opened. If you previously ran docker when mise forced `SECRET_KEY=dev`, run
   `mise run dev-reencrypt-secrets` once so tokens match your `.env` key, then export again.

2. Ensure `DEV_USER`, `DEV_PASSWORD`, and any connection vars you need are in `.env` (see
   `.env.example`).

3. Start the app, then bootstrap:

   ```bash
   mise run up-dev          # or dev-backend / up
   mise run dev-bootstrap   # creates user, logs in, saves connections, writes cookies.txt
   ```

Use `mise run dev-bootstrap -- --force` to re-save connections even when they already show `ok`.
Use `mise run dev-bootstrap -- --wait 60` if the API is slow to start.
