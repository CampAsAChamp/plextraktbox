# plextraktbox

All-in-one, self-hosted tool that keeps **Plex**, **Letterboxd**, and **Trakt** in sync — with a web UI, a built-in scheduler, live log streaming, and notifications.

It replaces stitching together two separate projects
([letterboxd-plex-sync](https://github.com/CampAsAChamp/letterboxd-plex-sync) and
[PlexTraktSync](https://github.com/Taxel/PlexTraktSync)) with one app, one UI, one scheduler.

See [PLAN.md](PLAN.md) for the full design doc and phase-by-phase progress tracker.

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
- **Deploy:** single Docker container (FastAPI serves the built SPA + runs the scheduler + SQLite). Target deployment environment is **TrueNAS** (SCALE) via its custom-app / "Launch Docker Image" flow, with `/data` mounted to a ZFS dataset — see [Deploying on TrueNAS](#deploying-on-truenas).

## Quick start (container)

One terminal — the image serves the API and built UI together on port 8000.

```bash
# First time only: cp .env.example .env and set PLEXTRAKTBOX_SECRET_KEY
mise run up   # or: podman compose up --build
# open http://localhost:8000 — setup wizard on first run, then login → dashboard
```

Install [mise](https://mise.jdx.dev/getting-started.html) for project tasks (`mise trust && mise install` on first clone). Run `mise tasks` to list everything.

See [docs/testing.md](docs/testing.md) for the full smoke-test checklist (including how to reset with `mise run down-v`).

## Local development

Use two terminals only when you want Vite hot reload while editing the frontend.

```bash
mise trust && mise install   # first time only
mise run install             # backend venv + frontend deps
mise run dev-backend         # terminal 1 — uvicorn on :8000
mise run dev-frontend        # terminal 2 — Vite on :5173
```

`mise` pins Python 3.12 and Node 22 (matching CI) and sets `PLEXTRAKTBOX_SECRET_KEY` / `PLEXTRAKTBOX_DATA_DIR` automatically.

Open the Vite URL (usually http://localhost:5173) for the dev SPA, or hit the backend directly once the SPA is built. Both `dev-backend` and `dev-frontend` must be running for the dev UI to show a green health badge.

## Deploying on TrueNAS

The intended install target is a **TrueNAS SCALE** box, not just any Docker host. Once the app is far
enough along to run a real scheduled job (see Phase 8 below), the deployment shape is:

- Run the built image via TrueNAS's **custom app** / "Launch Docker Image" flow (or a catalog app if one
  is published later) rather than assuming raw `docker run`/Compose access.
- Mount `/data` to a **ZFS dataset** (a host-path volume), not a Docker-managed volume, so the SQLite DB
  and caches live on the pool and survive app reinstalls.
- Expose a single HTTP port (8000) — no host networking, no privileged mode, no Docker-socket access, so
  it drops cleanly into TrueNAS's app UI.
- Respect the dataset's permission model: if the app needs a specific `PUID`/`PGID` to write to the
  mounted dataset, that's configured the same way other self-hosted TrueNAS apps handle it.

This isn't wired up yet — it's a deployment milestone (Phase 8) that follows once jobs, the scheduler,
and logging are in place, but the container has been kept dependency-free (single image, SQLite,
one port) from Phase 0 specifically so this drops in without rework.

### Getting into the TrueNAS App Catalog (Phase 9, later)

Running the container on the user's own box (Phase 8) is a separate milestone from getting
`plextraktbox` **listed in the TrueNAS App Catalog** so it can be installed like any official/community
app. That's a heavier, later effort with its own steps:

1. Package the app per TrueNAS SCALE's current app spec (a chart/`app.yaml`-style app definition with a
   config schema), not just a raw Docker image — check the current SCALE app format when this phase
   starts, since it has changed across releases.
2. Expose the user-configurable options (HTTP port, `/data` dataset path, `PLEXTRAKTBOX_SECRET_KEY`,
   etc.) through that config schema so they render as real fields in the TrueNAS app UI.
3. Publish the container image to a public registry (e.g. GHCR) with versioned tags — a catalog entry
   needs a real, pullable image, not a local build.
4. Submit to the official community catalog (via their contribution process) or stand up a self-hosted
   custom catalog added by URL — whichever fits — and confirm the current submission/review requirements
   at the time, since catalog mechanics are a moving target.
5. Verify the app installs and behaves correctly from the catalog on a clean TrueNAS instance.

Don't start this until Phase 8 (the personal install) has been running successfully for a while —
publishing before the app is proven on real hardware is premature.

## Tests & checks

```bash
mise run check   # lint + test (CI parity)
```

Or run each stack separately:

```bash
mise run test-backend
mise run test-frontend
```

## Build phases

The app is built incrementally; each phase is independently runnable and testable. See
[PLAN.md](PLAN.md#phase-tracker) for the checklist and current progress.
