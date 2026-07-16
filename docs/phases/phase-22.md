# Phase 22 — TrueNAS deployment (personal install)

**Status:** Done

## Goal

Run the built image on the user's own **TrueNAS SCALE** box via custom-app / "Launch Docker Image" —
no catalog involvement yet. Prove end-to-end on real hardware with a ZFS dataset mount.

This is **milestone 1** of two TrueNAS milestones (see [deploy/truenas.md](../deploy/truenas.md)).
Do not conflate with Phase 23 (catalog publication). TrueNAS work stays after product, ops, CI,
and release pipeline phases; [Phase 24](phase-24.md) (UI themes) shipped earlier on the roadmap.

## Deliverables

### Container permissions

- `PUID`/`PGID` env handling in [`docker/entrypoint.sh`](../../docker/entrypoint.sh) (`gosu` after
  `chown` of `/data`) so the app writes correctly to a ZFS-mounted dataset
- Ownership expectations documented in [deploy/truenas.md](../deploy/truenas.md)

### Published image

- **GHCR** with versioned tags — pull without local build ([Phase 19](phase-19.md))
- Package should be **public** for unauthenticated TrueNAS pulls (or use a registry credential)

### HTTPS / tunnel

- Document **Cloudflare Tunnel** in front of the TrueNAS app (HTTPS, `Secure` cookies). Any HTTPS
  terminator that forwards to port 8000 also works
- No host-network or privileged requirements

### Install documentation

- Step-by-step "Launch Docker Image" / custom-app setup in [deploy/truenas.md](../deploy/truenas.md)
- Env vars, port mapping, dataset mount path, `PUID`/`PGID`
- First-run wizard → connections → job → scheduled run → notification

### Real install verification

- Hardware checklist in [test-plans/phase-22-test-plan.md](test-plans/phase-22-test-plan.md)

## Constraints (from day one)

- Single container, SQLite, one HTTP port
- `/data` on ZFS host-path, not Docker-managed volume
- No Docker socket, no privileged mode, no macvlan

## Prerequisites

[Phases 7–8](phase-7.md) minimum (real movie sync); [Phase 11](phase-11.md) if TV is in scope before
deploy. Phases 13–14 strongly recommended for unattended operation.

**Release pipeline:** [Phase 19](phase-19.md) (GHCR publish) landed before this phase — see
[delivery order](README.md#delivery-order). [Phase 18](phase-18.md) (version in UI) is already done.

## Defers to later phases

| Item | Phase |
| ---- | ----- |
| TrueNAS App Catalog listing | 23 |

## Verification

[test-plans/phase-22-test-plan.md](test-plans/phase-22-test-plan.md) — local PUID smoke + real
hardware checklist (dataset permissions, cron, Cloudflare Tunnel HTTPS, notifications).

**Next:** [Phase 23 — TrueNAS catalog](phase-23.md) — only after Phase 22 runs successfully for a while
