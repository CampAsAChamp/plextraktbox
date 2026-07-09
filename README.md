# plextraktbox

All-in-one, self-hosted tool that keeps **Plex**, **Letterboxd**, and **Trakt** in sync — with a web UI, a built-in scheduler, live log streaming, and notifications.

It replaces stitching together two separate projects
([letterboxd-plex-sync](https://github.com/CampAsAChamp/letterboxd-plex-sync) and
[PlexTraktSync](https://github.com/Taxel/PlexTraktSync)) with one app, one UI, one scheduler.

## Sync model (source of truth per data type)

| Data type          | Source of truth | Direction                                             |
| ------------------ | --------------- | ----------------------------------------------------- |
| Watchlist          | **Plex**        | Reconcile Trakt to match Plex; Letterboxd read-only   |
| Ratings            | **Letterboxd**  | Push Letterboxd ratings → Plex and Trakt              |
| Watched / history  | **Trakt**       | Mark matched items watched in Plex; Letterboxd read   |

> Letterboxd is **read-only** — it has no usable write API for personal use.

## Stack

- **Backend:** Python 3.11+, FastAPI, SQLModel + Alembic, APScheduler, structlog. Reuses `plexapi` and `trakt.py`.
- **Frontend:** React + TypeScript + Vite, Mantine, TanStack Query.
- **Deploy:** single Docker container (FastAPI serves the built SPA + runs the scheduler + SQLite).

## Quick start (Docker)

```bash
cp .env.example .env
# set PLEXTRAKTBOX_SECRET_KEY (python -c "import secrets; print(secrets.token_urlsafe(48))")
docker compose up --build
# open http://localhost:8000 and complete the first-run wizard
```

## Local development

**Backend** (needs Python 3.11+):

```bash
cd backend
python3.12 -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
export PLEXTRAKTBOX_SECRET_KEY=dev PLEXTRAKTBOX_DATA_DIR=./data
alembic upgrade head
uvicorn plextraktbox.main:app --reload
```

**Frontend** (needs Node 20+):

```bash
cd frontend
npm install
npm run dev   # Vite proxies /api → http://localhost:8000
```

Open the Vite URL (http://localhost:5173) for the dev SPA, or hit the backend directly once the SPA is built.

## Tests & checks

```bash
# backend
cd backend && . .venv/bin/activate
ruff check plextraktbox && ruff format --check plextraktbox && mypy plextraktbox && pytest -q

# frontend
cd frontend && npm run typecheck && npm run test
```

## Build phases

The app is built incrementally; each phase is independently runnable and testable.

0. **Scaffold** ✅ — repo layout, health endpoint, single-container serving, CI.
1. Auth + first-run wizard (local user)
2. Connections + wizard steps (Plex / Trakt / Letterboxd / TMDB)
3. Sync engine core (sources + reconcilers + dry-run)
4. Jobs + runs + scheduler
5. Logging pipeline + live log viewer
6. Notifications (Discord / email / in-app)
7. Hardening
