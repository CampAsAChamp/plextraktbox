# Phase 0 verification checklist

Smoke tests for the scaffold. All four sections passed on 2026-07-10.

## 1. Container end-to-end

```bash
cp .env.example .env
python3 -c "import secrets; print(secrets.token_urlsafe(48))"   # paste into .env as PLEXTRAKTBOX_SECRET_KEY

podman compose up --build   # or: docker compose up --build
```

Then check:

- Build succeeds (frontend build stage, then Python runtime copy stage)
- `curl http://localhost:8000/api/health` → `{"status":"ok","version":"0.1.0"}`
- Open `http://localhost:8000/` in a browser → "plextraktbox" shell with a green "API ok" badge
- `podman compose down` then `podman compose up` again (no `--build`) → boots cleanly with the persisted volume

## 2. Local dev mode (day-to-day loop)

Both processes must be running — Vite proxies `/api` to the backend on port 8000.

```bash
# terminal 1 — backend (keep running)
cd backend && source .venv/bin/activate
PLEXTRAKTBOX_SECRET_KEY=dev PLEXTRAKTBOX_DATA_DIR=./data uvicorn plextraktbox.main:app --reload

# terminal 2 — frontend (keep running)
cd frontend && npm run dev
```

Open the URL Vite prints (usually `http://localhost:5173`) → same shell, badge should go green (proxied through Vite to the backend). Edit `App.tsx` and confirm hot-reload.

## 3. Built SPA served directly by the backend

```bash
cd frontend && npm run build
cd ../backend && source .venv/bin/activate
PLEXTRAKTBOX_SECRET_KEY=dev PLEXTRAKTBOX_DATA_DIR=./data uvicorn plextraktbox.main:app
```

Open `http://localhost:8000/` — exercises the `_mount_spa` static-file fallback, a different code path than the Vite dev proxy.

## 4. Quick sanity read

Skim [Dockerfile](../Dockerfile) and [docker-compose.yml](../docker-compose.yml) for the base images (`python:3.12-slim`, `node:22-alpine`). Confirm `.env` is not committed (`git status`).
