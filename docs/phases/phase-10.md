# Phase 10 — Frontend redesign

**Status:** Planned

## Goal

Replace the default Mantine admin-dashboard look with the **ops-console** direction validated in
[Phase 9](phase-9.md) — migrate all existing flows onto Radix + Tailwind and remove Mantine.
**No new sync features or API endpoints.**

## Design direction

Carry forward the approved Phase 9 prototype:

- Sidebar navigation (replace header nav + stacked sections)
- Split-pane run detail — promote prototype to production route
- Monospace for logs, run IDs, cron; distinct sans for UI chrome
- Intentional color system (charcoal base, amber/green status semantics)
- Consistent icon set (single library, one weight)
- Dense, repeat-use layouts for jobs/runs tables

## Stack

| Keep | Replace |
| ---- | ------- |
| React 18, Vite, TypeScript | Mantine components + default theme |
| TanStack Query, React Router | — |
| react-hook-form + zod | — |
| `@tanstack/react-virtual`, fetch-event-source | — |
| Vitest + RTL (+ MSW) | — |
| Phase 9 tokens + run-detail prototype | — |

**Styling:** Radix UI primitives + **Tailwind CSS** + project-owned design tokens. Do **not** adopt
shadcn/ui defaults wholesale.

## Deliverables

### Design system (extend Phase 9)

- Complete base component set: Input, Select, Alert, Table, Dialog, Menu, Nav
- Layout shell: sidebar + main content; account menu, notification bell, API health

### Page migration (existing flows)

Migrate to new components — behavior unchanged:

- Login, setup wizard, connections
- Jobs list / create / edit
- Run history + run detail + log viewer (from Phase 9 prototype)
- Dashboard (current minimal version)
- Settings (pre–Phase 13 scope: timezone/display prefs, notifications)

### UX polish

- Empty, loading, and error states
- Focus order, labels, contrast (accessibility basics)
- Light/dark theme via tokens (dark default)

### Cleanup

- Remove `@mantine/*` dependencies
- Delete prototype route/tree once production routes ship
- Update [architecture.md](../architecture.md) frontend stack

## Key files (expected)

- `frontend/src/components/ui/` — Radix + Tailwind primitives
- `frontend/src/components/layout/` — production shell
- `frontend/package.json` — Mantine removed

## Prerequisites

[Phase 9](phase-9.md) — prototype approved (go decision on look, layout, and log viewer)

## Defers to later phases

| Item | Phase |
| ---- | ----- |
| TV job form extensions | 11 |
| Settings page (global guards, backup) | 13 |
| GitHub Actions CI | 12 |
| Dashboard ops view, schedule picker, log export | 14 |
| Doppler maintainer workflow | 15 |
| TrueNAS packaging, GHCR, reverse proxy | 16 |

## Out of scope

- New sync data types, reconciler rules, or API endpoints
- TrueNAS / deployment changes

## Verification

Test plan TBD when phase lands — manual smoke across all migrated flows; Vitest/RTL tests updated;
Mantine fully removed from `package.json`.

**Next:** [Phase 11 — TV sync](phase-11.md)
