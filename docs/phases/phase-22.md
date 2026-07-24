# Phase 22 — TrueNAS deployment (personal install)

**Status:** Done

## Goal

Run the published image on the user's own **TrueNAS SCALE** box via custom app / "Launch Docker
Image" — no catalog involvement. Prove end-to-end on real hardware with a ZFS dataset mount.

This is **milestone 1** of two TrueNAS milestones (see [deploy/truenas.md](../deploy/truenas.md)).
Do not conflate with [Phase 23](phase-23.md) (catalog publication).

## Deliverables

- `PUID`/`PGID` in [`docker/entrypoint.sh`](../../docker/entrypoint.sh) (`su-exec` after `chown` of
  `/data`) so the app writes correctly to a ZFS-mounted dataset
- GHCR image with versioned tags; package **public** for unauthenticated TrueNAS pulls (or a
  registry credential)
- Cloudflare Tunnel (or any HTTPS terminator) documented for Secure cookies / LAN HTTP via
  adaptive `SESSION_HTTPS_ONLY`
- Step-by-step custom-app setup in [deploy/truenas.md](../deploy/truenas.md)

## Constraints

- Single container, SQLite, one HTTP port
- `/data` on ZFS host-path, not a Docker-managed volume
- No Docker socket, no privileged mode, no host networking

## Verification

[test-plans/phase-22-test-plan.md](test-plans/phase-22-test-plan.md)

**Next:** [Phase 23 — TrueNAS catalog](phase-23.md) — only after this personal install has run
successfully for a while.
