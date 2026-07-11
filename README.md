<a name="readme-top"></a>

<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/CampAsAChamp/plextraktbox">
    <img src="docs/imgs/logo.png" alt="plextraktbox logo" width="200" height="200">
  </a>

  <h3 align="center">plextraktbox</h3>

  <p align="center">
    All-in-one, self-hosted tool that keeps Plex, Letterboxd, and Trakt in sync — with a web UI, built-in scheduler, live log streaming, and notifications.
    <br />
    <br />
    <a href="PLAN.md"><strong>Explore the design doc »</strong></a>
    <br />
    <br />
    <a href="docs/testing.md">Testing guide</a>
    ·
    <a href="https://github.com/CampAsAChamp/plextraktbox/issues">Report Bug</a>
    ·
    <a href="https://github.com/CampAsAChamp/plextraktbox/issues">Request Feature</a>
  </p>
</div>

<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
      <ul>
        <li><a href="#sync-model">Sync Model</a></li>
        <li><a href="#built-with">Built With</a></li>
      </ul>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#quick-start-container">Quick Start (Container)</a></li>
        <li><a href="#local-development">Local Development</a></li>
      </ul>
    </li>
    <li><a href="#deploying-on-truenas">Deploying on TrueNAS</a></li>
    <li><a href="#tests--checks">Tests &amp; Checks</a></li>
    <li><a href="#roadmap">Roadmap</a></li>
    <li><a href="#acknowledgments">Acknowledgments</a></li>
  </ol>
</details>

<!-- ABOUT THE PROJECT -->
## About The Project

It replaces stitching together two separate projects — [letterboxd-plex-sync](https://github.com/CampAsAChamp/letterboxd-plex-sync) and [PlexTraktSync](https://github.com/Taxel/PlexTraktSync) — with one app, one UI, and one scheduler.

See [PLAN.md](PLAN.md) for the full design doc and phase-by-phase progress tracker.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Sync Model

Source of truth per data type:

| Data type         | Source of truth | Direction                                           |
| ----------------- | --------------- | --------------------------------------------------- |
| Watchlist         | **Plex**        | Reconcile Trakt to match Plex; Letterboxd read-only |
| Ratings           | **Letterboxd**  | Push Letterboxd ratings → Plex and Trakt            |
| Watched / history | **Trakt**       | Mark matched items watched in Plex; Letterboxd read |

> Letterboxd is **read-only** — it has no usable write API for personal use.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Built With

[![My Skills](https://skillicons.dev/icons?i=python,fastapi,react,ts,docker,vite,sqlite,linux)](https://skillicons.dev)

* [Python 3.14](https://www.python.org/) + [FastAPI](https://fastapi.tiangolo.com/) — backend API, scheduler, sync engine
* [SQLModel](https://sqlmodel.tiangolo.com/) + [Alembic](https://alembic.sqlalchemy.org/) — SQLite persistence and migrations
* [APScheduler](https://apscheduler.readthedocs.io/) + [structlog](https://www.structlog.org/) — job scheduling and structured logging
* [plexapi](https://github.com/pkkid/python-plexapi) + [trakt.py](https://github.com/fuzion24/Trakt.py) — Plex and Trakt clients
* [React 18](https://react.dev/) + [TypeScript](https://www.typescriptlang.org/) + [Vite](https://vitejs.dev/) — SPA frontend
* [Mantine](https://mantine.dev/) + [TanStack Query](https://tanstack.com/query) — UI components and data fetching
* Single [Docker](https://www.docker.com/) container — FastAPI serves the built SPA, runs the scheduler, and stores data on a `/data` volume

Target deployment environment is **TrueNAS SCALE** via its custom-app / "Launch Docker Image" flow, with `/data` mounted to a ZFS dataset — see [Deploying on TrueNAS](#deploying-on-truenas).

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- GETTING STARTED -->
## Getting Started

### Prerequisites

* [mise](https://mise.jdx.dev/getting-started.html) — pins Python 3.14, Node 24, and jq and defines project tasks
* [Docker](https://docs.docker.com/get-docker/) or [Podman](https://podman.io/) — for container workflows (`mise run up`, `mise run up-dev`)

### Quick Start (Container)

One terminal — the image serves the API and built UI together on port 8000.

```bash
# First time only: cp .env.example .env and set SECRET_KEY (and Trakt API app credentials for the Trakt onboarding step)
mise trust && mise install   # first clone only
mise run up                  # or: podman compose up --build
# open http://localhost:8000 — setup wizard on first run, then login → dashboard
```

Run `mise tasks` to list everything. See [docs/testing.md](docs/testing.md) for the full smoke-test checklist (including how to reset with `mise run down-v`).

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Local Development

Hot reload while editing — pick one approach:

**Container dev (one terminal):**

```bash
mise run up-dev   # backend :8000 + Vite :5173 with bind mounts and reload
# open http://localhost:5173
mise run down-dev
```

`up-dev` runs `compose up --build`, which rebuilds images when Dockerfiles or dependency files change, but still uses layer cache. After changing `pyproject.toml` or `package.json`, use `mise run rebuild-dev` for a no-cache image rebuild (also recreates the frontend `node_modules` volume). Source edits under `backend/` and `frontend/` reload live via bind mounts — no rebuild needed for those.

**Native dev (two terminals, no Docker):**

```bash
mise trust && mise install   # first time only
mise run install             # backend venv + frontend deps
mise run dev-backend         # terminal 1 — uvicorn on :8000
mise run dev-frontend        # terminal 2 — Vite on :5173
```

Native dev and docker both use `./data` at the repo root (`DATA_DIR` in `.env`). Open the Vite URL (usually http://localhost:5173) for the dev SPA. Both backend and frontend must be running for the health badge to go green.

Do not run `up` and `up-dev` at the same time — they both bind port 8000.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- DEPLOYING ON TRUENAS -->
## Deploying on TrueNAS

The intended install target is a **TrueNAS SCALE** box, not just any Docker host. Once the app is far enough along to run a real scheduled job (see [Roadmap](#roadmap)), the deployment shape is:

* Run the built image via TrueNAS's **custom app** / "Launch Docker Image" flow (or a catalog app if one is published later) rather than assuming raw `docker run`/Compose access.
* Mount `/data` to a **ZFS dataset** (a host-path volume), not a Docker-managed volume, so the SQLite DB and caches live on the pool and survive app reinstalls.
* Expose a single HTTP port (8000) — no host networking, no privileged mode, no Docker-socket access, so it drops cleanly into TrueNAS's app UI.
* Respect the dataset's permission model: if the app needs a specific `PUID`/`PGID` to write to the mounted dataset, that's configured the same way other self-hosted TrueNAS apps handle it.

This isn't wired up yet — it's a deployment milestone (Phase 8) that follows once jobs, the scheduler, and logging are in place, but the container has been kept dependency-free (single image, SQLite, one port) from Phase 0 specifically so this drops in without rework.

### Getting into the TrueNAS App Catalog (Phase 9, later)

Running the container on the user's own box (Phase 8) is a separate milestone from getting `plextraktbox` **listed in the TrueNAS App Catalog** so it can be installed like any official/community app. That's a heavier, later effort with its own steps:

1. Package the app per TrueNAS SCALE's current app spec (a chart/`app.yaml`-style app definition with a config schema), not just a raw Docker image — check the current SCALE app format when this phase starts, since it has changed across releases.
2. Expose the user-configurable options (HTTP port, `/data` dataset path, `SECRET_KEY`, etc.) through that config schema so they render as real fields in the TrueNAS app UI.
3. Publish the container image to a public registry (e.g. GHCR) with versioned tags — a catalog entry needs a real, pullable image, not a local build.
4. Submit to the official community catalog (via their contribution process) or stand up a self-hosted custom catalog added by URL — whichever fits — and confirm the current submission/review requirements at the time, since catalog mechanics are a moving target.
5. Verify the app installs and behaves correctly from the catalog on a clean TrueNAS instance.

Don't start this until Phase 8 (the personal install) has been running successfully for a while — publishing before the app is proven on real hardware is premature.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- TESTS & CHECKS -->
## Tests & Checks

```bash
mise run check   # lint + test (CI parity)
```

Or run each stack separately:

```bash
mise run test-backend
mise run test-frontend
```

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- ROADMAP -->
## Roadmap

The app is built incrementally; each phase is independently runnable and testable. See [PLAN.md#phase-tracker](PLAN.md#phase-tracker) for the checklist and current progress.

- [x] **Phase 0 — Scaffold** — layout, Docker, compose, config, DB, health endpoint
- [x] **Phase 1 — Auth + wizard** — single local user, sessions, setup gate
- [x] **Phase 2 — Connections** — Plex, Trakt, Letterboxd, TMDB connection flows
- [x] **Phase 3 — Sync engine core** — matching, reconcilers, dry-run engine
- [ ] **Phase 4 — Jobs + runs + scheduler** — job CRUD, APScheduler, run history UI
- [x] **Phase 5 — Logging pipeline + live viewer** — structlog, SSE, LogViewer
- [ ] **Phase 6 — Notifications** — Discord, email, in-app alerts
- [ ] **Phase 7 — Hardening** — retention, CI, polish, OpenAPI → TS types
- [ ] **Phase 8 — TrueNAS deployment (personal install)** — real install on user's box
- [ ] **Phase 9 — TrueNAS App Catalog publication** — packaged app + public image
- [ ] **Phase 10 — Doppler secret management** — optional maintainer dev/CI workflow

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- ACKNOWLEDGMENTS -->
## Acknowledgments

* [othneildrew/Best-README-Template](https://github.com/othneildrew/Best-README-Template) — README structure
* [CampAsAChamp/letterboxd-plex-sync](https://github.com/CampAsAChamp/letterboxd-plex-sync) — Letterboxd → Plex sync inspiration
* [Taxel/PlexTraktSync](https://github.com/Taxel/PlexTraktSync) — Plex ↔ Trakt sync engine patterns
* [skillicons.dev](https://skillicons.dev) — tech stack badges

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- MARKDOWN LINKS & IMAGES -->
[stars-shield]: https://img.shields.io/github/stars/CampAsAChamp/plextraktbox.svg?style=for-the-badge
[stars-url]: https://github.com/CampAsAChamp/plextraktbox/stargazers
[issues-shield]: https://img.shields.io/github/issues/CampAsAChamp/plextraktbox.svg?style=for-the-badge
[issues-url]: https://github.com/CampAsAChamp/plextraktbox/issues
