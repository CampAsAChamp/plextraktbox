# Phase 13 — TrueNAS App Catalog publication

**Status:** Planned

## Goal

Get **plextraktbox** listed in the **TrueNAS App Catalog** so anyone can install it like an
official/community app — not just via manual "Launch Docker Image."

This is **milestone 2** of two TrueNAS milestones (see [deploy/truenas.md](../deploy/truenas.md)).
**Do not start until Phase 12 has been running
successfully on real hardware for a while** — publishing before the app is proven is premature.

## Deliverables

### App packaging

- Package per **current TrueNAS SCALE app spec** (chart / `app.yaml`-style definition with config
  schema) — verify format at phase start; it changes across SCALE releases
- Config schema exposes user-facing fields: HTTP port, `/data` dataset path, `SECRET_KEY`, Trakt app
  credentials, etc. — not raw env-only compose

### Image registry

- Public registry (e.g. GHCR) with **versioned tags** — catalog cannot point at local-only images

### Catalog submission

- Submit to official community catalog **or** stand up a self-hosted custom catalog URL
- Confirm current submission/review requirements at phase start (catalog mechanics move over time)
- Pass TrueNAS validation/review

### Verification

- Clean TrueNAS instance installs from catalog UI
- App behaves identically to Phase 12 manual install

## Prerequisites

[Phase 12](phase-12.md) — personal install stable on real hardware

## Notes

See [deploy/truenas.md](../deploy/truenas.md) for the two-milestone overview. This doc is the
implementation checklist for catalog work.

## Verification

Test plan TBD — catalog install on clean SCALE box.

**Next:** [Phase 14 — Doppler secrets](phase-14.md)
