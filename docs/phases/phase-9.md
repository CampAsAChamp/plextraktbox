# Phase 9 — Frontend prototype

**Status:** Planned

## Goal

Validate the **ops-console** UI direction before committing to a full frontend rewrite. Build a
**standalone prototype** of run detail + live log viewer on Radix + Tailwind with real sync data —
without migrating the rest of the app off Mantine yet.

If the prototype feels wrong, pivot here cheaply. Phase 10 carries the approved direction across all
pages.

## Deliverables

### Stack spike

- Add Tailwind CSS + Radix UI to the frontend (coexists briefly with Mantine)
- Design tokens: color, typography (UI sans + log monospace), spacing, radius
- 3–5 base primitives needed for the prototype (Button, Badge, ScrollArea, etc.)

### Prototype screens

- **Run detail** — split pane: run summary + counts left, live log stream right
- **Log viewer chrome** — monospace stream, level coloring, live SSE indicator, virtualized scroll
- Route reachable from existing run history (feature flag, `/runs/:id/v2`, or parallel route — TBD
  at implementation)

### Design validation

- Ops-console aesthetic: charcoal base, amber/green status semantics (not Mantine default blue)
- Sidebar or minimal chrome — enough to judge layout density and hierarchy
- Test with **real job runs** from Phases 7–8 (non-zero fetch/plan/apply logs)

### Exit criteria (go / no-go for Phase 10)

- [ ] Prototype readable for long log sessions (contrast, density, font choice)
- [ ] Live SSE stream feels good in the new layout
- [ ] Split-pane run detail works on desktop; acceptable fallback on mobile
- [ ] You would ship this look — not another vibe-coded dashboard

## Key files (expected)

- `frontend/src/prototype/` or `frontend/src/features/run-detail-v2/` — isolated prototype tree
- `frontend/tailwind.config.*`, token/CSS files
- Existing `LogViewer` SSE logic reused or wrapped — no backend changes

## Prerequisites

[Phase 8](phase-8.md) — movie fetch + apply working so the prototype exercises real run data and
logs

## Defers to later phases

| Item | Phase |
| ---- | ----- |
| Full app migration off Mantine | 10 |
| Sidebar shell + all pages | 10 |
| TV job form extensions | 11 |
| Settings page (global guards, backup, CI) | 12 |
| Dashboard ops view, schedule picker | 13 |

## Out of scope

- Migrating login, wizard, connections, jobs list, dashboard, or settings off Mantine
- Removing `@mantine/*` dependencies (Phase 10)
- New sync features or API endpoints

## Verification

Test plan TBD when phase lands — manual review of prototype with real runs; optional screenshot
checklist for go/no-go before Phase 10.

**Next:** [Phase 10 — Frontend redesign](phase-10.md)
