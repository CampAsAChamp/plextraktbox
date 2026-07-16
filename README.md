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
    <a href="docs/README.md"><strong>Documentation »</strong></a>
    <br />
    <a href="docs/architecture.md">Architecture</a>
    ·
    <a href="docs/phases/README.md">Roadmap</a>
    <br />
    <br />
    <a href="docs/testing.md">Testing guide</a>
    ·
    <a href="docs/dev-workflow.md">Dev workflow</a>
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
    <li><a href="#releases">Releases</a></li>
    <li><a href="#tests--checks">Tests &amp; Checks</a></li>
    <li><a href="#roadmap">Roadmap</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#acknowledgments">Acknowledgments</a></li>
  </ol>
</details>

<!-- ABOUT THE PROJECT -->
## About The Project

It replaces stitching together two separate projects — [letterboxd-plex-sync](https://github.com/CampAsAChamp/letterboxd-plex-sync) and [PlexTraktSync](https://github.com/Taxel/PlexTraktSync) — with one app, one UI, and one scheduler.

See [docs/architecture.md](docs/architecture.md) for design and locked decisions.
[docs/phases/](docs/phases/) has remaining work; [docs/README.md](docs/README.md) is the doc index.

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

Target deployment environment is **TrueNAS SCALE** — see [docs/deploy/truenas.md](docs/deploy/truenas.md).

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- GETTING STARTED -->
## Getting Started

### Prerequisites

* [mise](https://mise.jdx.dev/getting-started.html) — pins Python 3.14, Node 24, and jq and defines project tasks
* [Podman](https://podman.io/) — for container workflows (`mise run up`, `mise run up-dev`)

### Quick Start (Container)

One terminal — the image serves the API and built UI together on port 8000 (override with
`PORT` in `.env`; host and container ports both follow that value).

```bash
# Maintainers: doppler login && doppler setup (secrets in Doppler; see docs/dev-workflow.md)
# Without Doppler: cp .env.example .env and set SECRET_KEY + Trakt API app credentials
mise trust && mise install   # first clone only
mise run up-doppler          # prod container with Doppler; or: mise run up with a filled .env
# open http://localhost:8000 — setup wizard on first run, then login → dashboard
```

Run `mise tasks` to list everything. See [docs/testing.md](docs/testing.md) for smoke tests and
[docs/dev-workflow.md](docs/dev-workflow.md) for hot reload, Doppler, and dev bootstrap.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Local Development

Hot reload while editing — pick one approach:

**Container dev (one terminal):**

```bash
mise run up-dev   # Doppler + backend :8000 + Vite :5173 with bind mounts and reload
# open http://localhost:5173
mise run down-dev
```

`up-dev` wraps `doppler run -- compose up --build` and waits for a clean `compose down` on Ctrl+C (use `up-dev-env` if secrets are only in `.env`). After changing `pyproject.toml` or `package.json`, use `mise run rebuild-dev` for a no-cache image rebuild (also recreates the frontend `node_modules` volume). Source edits under `backend/` and `frontend/` reload live via bind mounts — no rebuild needed for those.

**Native dev (two terminals, no Docker):**

```bash
mise trust && mise install   # first time only
mise run install             # backend venv + frontend deps + commit hooks
doppler run -- mise run dev-backend   # terminal 1 — uvicorn on :8000
mise run dev-frontend              # terminal 2 — Vite on :5173
```

Native dev and docker both use `./data` at the repo root (`DATA_DIR` in `.env`). Open the Vite URL (usually http://localhost:5173) for the dev SPA. Both backend and frontend must be running for the health badge to go green.

Do not run `up` and `up-dev` at the same time — they both bind the HTTP listen port (default 8000).

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- DEPLOYING ON TRUENAS -->
## Deploying on TrueNAS

The intended install target is **TrueNAS SCALE** (custom app / "Launch Docker Image", `/data` on a ZFS
dataset, single HTTP port, Cloudflare Tunnel for HTTPS). Full install steps:
**[docs/deploy/truenas.md](docs/deploy/truenas.md)**. App Catalog publication is
[Phase 23](docs/phases/phase-23.md).

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- RELEASES -->
## Releases

Version source of truth is `backend/pyproject.toml` (shown in the UI via `/api/health`). Container
images publish to GHCR on each GitHub Release.

**Cutting a release**

1. Land changes on `main` with a [Conventional Commit](https://www.conventionalcommits.org/)
   subject (`feat: …`, `fix: …`, `feat!: …`) — either a direct push or a squash-merge PR
   title. A local `commit-msg` hook (enabled by `mise run install`) and
   `.github/workflows/pr-title.yml` enforce the format. The same install enables a
   `pre-push` hook that runs `mise run check` before push.
2. [semantic-release](https://semantic-release.gitbook.io/) bumps the one app semver (root
   `package.json`, `backend/pyproject.toml`, `frontend/package.json`, `CHANGELOG.md`), creates tag
   `vX.Y.Z` + a GitHub Release, and publishes `ghcr.io/campasachamp/plextraktbox:vX.Y.Z` (+ `:latest`)
   — no Release PR to merge.

**Pull a release image**

```bash
docker pull ghcr.io/campasachamp/plextraktbox:vX.Y.Z
```

After the first publish, set the GitHub Packages package visibility to **public** if you need
unauthenticated pulls (e.g. TrueNAS). Manual tags (`git push origin vX.Y.Z`) also publish via
`.github/workflows/release.yml`. Prefer squash-merge on `main`.

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

Product development is done. Remaining work: TrueNAS App Catalog ([Phase 23](docs/phases/phase-23.md))
— see [docs/phases/README.md](docs/phases/README.md). Settings supports SQLite backup download and
restore; on TrueNAS prefer ZFS snapshots of the `/data` dataset for routine backups.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- LICENSE -->
## License

Distributed under the MIT License. See [`LICENSE`](LICENSE) for details. Security reports:
[`SECURITY.md`](SECURITY.md).

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
