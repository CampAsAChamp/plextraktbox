# Phase 0 verification checklist

Smoke tests for the scaffold. All four sections passed on 2026-07-10.

Shared setup and mise tasks: [testing.md](testing.md).

## 1. Container end-to-end

```bash
# First time only: cp .env.example .env and set SECRET_KEY

mise run up   # or: podman compose up --build
```

Then check:

- Build succeeds (frontend build stage, then Python runtime copy stage)
- `curl http://localhost:8000/api/health` → `{"status":"ok","version":"0.1.0"}`
- Open `http://localhost:8000/` in a browser → "plextraktbox" shell with a green "API ok" badge
- `mise run down` then `mise run up` again (no rebuild) → boots cleanly with the persisted volume

## 2. Local dev mode (two terminals — hot reload only)

Both processes must be running — Vite proxies `/api` to the backend on port 8000.

```bash
mise run dev-backend    # terminal 1
mise run dev-frontend   # terminal 2
```

Open the URL Vite prints (usually `http://localhost:5173`) → same shell, badge should go green (proxied through Vite to the backend). Edit `App.tsx` and confirm hot-reload.

## 3. Built SPA served directly by the backend

```bash
cd frontend && npm run build
cd ../backend && source .venv/bin/activate
SECRET_KEY=dev DATA_DIR=./data uvicorn plextraktbox.main:app
```

Open `http://localhost:8000/` — exercises the `_mount_spa` static-file fallback, a different code path than the Vite dev proxy.

## 4. Quick sanity read

Skim [Dockerfile](../Dockerfile) and [docker-compose.yml](../docker-compose.yml) for the base images (`python:3.12-slim`, `node:22-alpine`). Confirm `.env` is not committed (`git status`).
