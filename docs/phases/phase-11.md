# Phase 11 — TrueNAS deployment (personal install)

**Status:** Planned

## Goal

Run the built image on the user's own **TrueNAS SCALE** box via custom-app / "Launch Docker Image" —
no catalog involvement yet. Prove end-to-end on real hardware with a ZFS dataset mount.

This is **milestone 1** of two TrueNAS milestones (see [deploy/truenas.md](../deploy/truenas.md)).
Do not conflate with Phase 12 (catalog publication).

## Deliverables

### Container permissions

- Confirm `PUID`/`PGID`-style env handling so the app writes correctly to a ZFS-mounted `/data`
  dataset
- Document ownership expectations in [deploy/truenas.md](../deploy/truenas.md)

### Published image

- **GHCR** (or equivalent) with versioned tags — pull without local build
- Release tagging workflow documented

### Reverse proxy / TLS

- Document Caddy or Traefik example in front of the TrueNAS app (HTTPS, `Secure` cookies)
- No host-network or privileged requirements

### Install documentation

- Step-by-step "Launch Docker Image" / custom-app setup in [deploy/truenas.md](../deploy/truenas.md)
- Env vars, port mapping, dataset mount path
- First-run wizard → connections → job → scheduled run → notification

### Real install verification

- End-to-end on user's TrueNAS hardware: wizard, cron job fires, logs stream, Discord/in-app notify

## Constraints (from day one)

- Single container, SQLite, one HTTP port
- `/data` on ZFS host-path, not Docker-managed volume
- No Docker socket, no privileged mode, no macvlan

## Prerequisites

[Phase 7](phase-7.md) minimum (real movie sync); [Phase 10](phase-10.md) if TV is in scope before
deploy. Phases 8–9 strongly recommended for unattended operation.

## Defers to later phases

| Item | Phase |
| ---- | ----- |
| TrueNAS App Catalog listing | 12 |
| Doppler maintainer workflow | 13 |

## Verification

Test plan TBD — real hardware checklist (dataset permissions, cron, TLS, notifications).

**Next:** [Phase 12 — TrueNAS catalog](phase-12.md) — only after Phase 11 runs successfully for a while
