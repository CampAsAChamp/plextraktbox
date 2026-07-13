# Deploying on TrueNAS

The intended install target is **TrueNAS SCALE**, not just any Docker host. The container has been
kept dependency-free (single image, SQLite, one HTTP port) from Phase 0 so it drops into TrueNAS
without rework.

**Status:** Not wired up yet — personal install is [Phase 12](../phases/phase-12.md); catalog
publication is [Phase 13](../phases/phase-13.md).

## Design constraints (all environments)

These apply whenever touching Dockerfile, compose, or entrypoint — not only at deploy time:

- **Single container** — FastAPI serves the SPA, runs the scheduler, SQLite on `/data`
- **`/data` on a ZFS dataset** — host-path mount, not a Docker-managed volume, so the DB survives
  app reinstalls
- **One HTTP port** (8000) — no host networking, no privileged mode, no Docker-socket access
- **No hardcoded UIDs** — support `PUID`/`PGID`-style env vars so file ownership on the mounted
  dataset behaves on TrueNAS
- Ship via TrueNAS **Apps** (custom app / "Launch Docker Image" workflow, or catalog app later)

See [architecture.md](../architecture.md) for full stack context.

## Milestone 1 — Personal install (Phase 12)

Run the built image on your own TrueNAS box via **custom app** / "Launch Docker Image". No catalog
involvement — a working container + dataset mount on one machine.

**Near-term deliverables** (see [phase-12](../phases/phase-12.md)):

- Confirm `PUID`/`PGID` against a real ZFS dataset mount
- Publish versioned image to GHCR (pull without local build)
- Document reverse proxy / TLS (Caddy or Traefik example; `Secure` session cookies)
- Step-by-step custom-app setup: env vars, port, dataset path
- End-to-end proof: wizard → connections → job → scheduled run → notification

## Milestone 2 — App Catalog (Phase 13)

Getting **plextraktbox** **listed in the TrueNAS App Catalog** is a separate, heavier effort. Do
**not** start until Phase 12 has run successfully on real hardware for a while.

**Catalog deliverables** (see [phase-13](../phases/phase-13.md)):

1. Package per current TrueNAS SCALE app spec (chart / `app.yaml`-style definition with config
   schema) — verify format at phase start; it changes across SCALE releases
2. Expose user-configurable options (HTTP port, `/data` path, `SECRET_KEY`, etc.) through the
   TrueNAS app config UI, not raw env-only compose
3. Publish container image to a public registry (e.g. GHCR) with versioned tags
4. Submit to the official community catalog or stand up a self-hosted custom catalog URL — confirm
   current submission/review requirements at the time
5. Verify catalog install on a clean TrueNAS instance

## Quick reference (Phase 12 install shape)

When Phase 12 lands, expect roughly:

| Setting | Value |
| ------- | ----- |
| Image | GHCR tagged release (TBD) |
| Port | 8000 → app HTTP |
| Volume | Host path → `/data` (ZFS dataset) |
| Env | `SECRET_KEY`, `TRAKT_CLIENT_ID`, `TRAKT_CLIENT_SECRET`, optional `PUID`/`PGID` |

Detailed install steps will be added here as Phase 12 is implemented.
