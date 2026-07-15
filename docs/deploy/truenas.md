# Deploying on TrueNAS

The intended install target is **TrueNAS SCALE**, not just any Docker host. The container has been
kept dependency-free (single image, SQLite, one HTTP port) from Phase 0 so it drops into TrueNAS
without rework.

**Status:** Not wired up yet — personal install is [Phase 22](../phases/phase-22.md); catalog
publication is [Phase 23](../phases/phase-23.md). Both come after product, ops, CI, and release
pipeline phases. [Phase 24](../phases/phase-24.md) (UI themes) is done — optional themes volume below.

## Design constraints (all environments)

These apply whenever touching Dockerfile, compose, or entrypoint — not only at deploy time:

- **Single container** — FastAPI serves the SPA, runs the scheduler, SQLite on `/data`
- **`/data` on a ZFS dataset** — host-path mount, not a Docker-managed volume, so the DB survives
  app reinstalls. Prefer ZFS snapshots of that dataset for routine backups; Settings also offers an
  ad-hoc SQLite download (`GET /api/settings/backup`).
- **One HTTP port** (8000) — no host networking, no privileged mode, no Docker-socket access
- **No hardcoded UIDs** — support `PUID`/`PGID`-style env vars so file ownership on the mounted
  dataset behaves on TrueNAS
- Ship via TrueNAS **Apps** (custom app / "Launch Docker Image" workflow, or catalog app later)
- **Secrets via app env / `.env`** — do not require [Doppler](https://www.doppler.com/). Doppler is
  optional for maintainers in local/CI only ([Phase 15](../phases/phase-15.md))

See [architecture.md](../architecture.md) for full stack context.

## Milestone 1 — Personal install (Phase 22)

Run the built image on your own TrueNAS box via **custom app** / "Launch Docker Image". No catalog
involvement — a working container + dataset mount on one machine.

**Near-term deliverables** (see [phase-22](../phases/phase-22.md)):

- Confirm `PUID`/`PGID` against a real ZFS dataset mount
- Pull versioned image from GHCR (no local build) — [Phase 19](../phases/phase-19.md) done; tags below
- Document reverse proxy / TLS (Caddy or Traefik example; `Secure` session cookies)
- Step-by-step custom-app setup: env vars, port, dataset path
- End-to-end proof: wizard → connections → job → scheduled run → notification

## Milestone 2 — App Catalog (Phase 23)

Getting **plextraktbox** **listed in the TrueNAS App Catalog** is a separate, heavier effort. Do
**not** start until Phase 22 has run successfully on real hardware for a while.

**Catalog deliverables** (see [phase-23](../phases/phase-23.md)):

1. Package per current TrueNAS SCALE app spec (chart / `app.yaml`-style definition with config
   schema) — verify format at phase start; it changes across SCALE releases
2. Expose user-configurable options (HTTP port, `/data` path, `SECRET_KEY`, etc.) through the
   TrueNAS app config UI, not raw env-only compose
3. Publish container image to a public registry (e.g. GHCR) with versioned tags
4. Submit to the official community catalog or stand up a self-hosted custom catalog URL — confirm
   current submission/review requirements at the time
5. Verify catalog install on a clean TrueNAS instance

## Quick reference (Phase 22 install shape)

When Phase 22 lands, expect roughly:

| Setting | Value |
| ------- | ----- |
| Image | `ghcr.io/campasachamp/plextraktbox:vX.Y.Z` (or `:latest`) |
| Port | 8000 → app HTTP |
| Volume | Host path → `/data` (ZFS dataset) |
| Env | `SECRET_KEY`, `TRAKT_CLIENT_ID`, `TRAKT_CLIENT_SECRET`, optional `PUID`/`PGID` |

### Optional UI themes volume ([Phase 24](../phases/phase-24.md))

Custom theme CSS files are discovered from `{DATA_DIR}/themes/*.css` (same path as Settings
upload). With the usual `/data` mount that is already `/data/themes` inside the container — no
extra mount required. If you prefer a separate host folder:

```yaml
volumes:
  - /mnt/tank/apps/plextraktbox/data:/data
  # Optional second path only if themes live outside the main dataset:
  # - /mnt/tank/apps/plextraktbox/themes:/data/themes
```

Format notes: [phase-24.md](../phases/phase-24.md) and `frontend/src/themes/README.md`.

### GHCR image ([Phase 19](../phases/phase-19.md))

Published on each GitHub Release:

| Tag | Meaning |
| --- | ------- |
| `ghcr.io/campasachamp/plextraktbox:vX.Y.Z` | Immutable release matching `backend/pyproject.toml` |
| `ghcr.io/campasachamp/plextraktbox:latest` | Most recent stable release |

```bash
docker pull ghcr.io/campasachamp/plextraktbox:v0.1.0
```

The package must be **public** on GitHub Packages for unauthenticated pulls (set after the first
publish). Full custom-app install steps land in Phase 22.
