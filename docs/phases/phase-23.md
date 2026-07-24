# Phase 23 — TrueNAS App Catalog publication

**Status:** Planned

## Goal

Get **plextraktbox** listed in the **TrueNAS App Catalog** so anyone can install it like an
official/community app — not just via manual "Launch Docker Image."

This is **milestone 2** of two TrueNAS milestones (see [deploy/truenas.md](../deploy/truenas.md)).
**Do not start until the personal install has been running successfully on real hardware for a
while** ([Phase 22](phase-22.md)) — publishing before the app is proven is premature.

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
- App behaves identically to the manual personal install documented in
  [deploy/truenas.md](../deploy/truenas.md)

## Prerequisites

Personal TrueNAS install stable on real hardware
([phase-22](phase-22.md) / [deploy/truenas.md](../deploy/truenas.md)).

## Notes

See [deploy/truenas.md](../deploy/truenas.md) for the two-milestone overview. This doc is the
implementation checklist for catalog work.

## Verification

Full pre-upload checklist:
[test-plans/phase-23-test-plan.md](test-plans/phase-23-test-plan.md)
(clean catalog install, packaging, sync smoke, upgrade/persistence).
