# Phase 20 — Mobile & responsive layout

**Status:** Planned

## Goal

Make the full SPA usable on phones and small tablets — not a separate mobile app, but a responsive
layout that preserves every flow from desktop. Ops-console density on large screens; readable,
touch-friendly layouts below ~768px.

**No new sync features or API endpoints.**

## Context

The app is built for repeat desktop use (sidebar, wide tables, split-pane run detail). Viewport meta
is already set; the gap is layout, navigation, and component behavior at narrow widths. Do this **after**
the Radix + Tailwind migration ([Phase 10](phase-10.md)) and major UX flows ([Phase 14](phase-14.md))
so responsive work targets the final component set.

## Deliverables

### Layout shell

- **Breakpoint strategy** — document tokens (e.g. `sm` / `md` / `lg`) in the design system; default
  mobile-first where practical
- **Sidebar → drawer** — collapsible nav on small viewports; hamburger or equivalent; focus trap +
  escape to close
- **Header compaction** — version badge, health, notification bell, account menu usable without
  horizontal scroll
- **Safe areas** — respect notches / home indicators where relevant (`env(safe-area-inset-*)`)

### Page-level responsive patterns

Apply consistently across all routes:

| Area | Desktop (keep) | Mobile |
| ---- | -------------- | ------ |
| Jobs / run history tables | Dense tables | Card list or scrollable table; priority columns only |
| Run detail | Split pane (summary + logs) | Stacked sections; log viewer full width |
| Log viewer | Virtualized monospace pane | Readable font size; level filters in sheet/drawer |
| Connections wizard | Multi-step forms | Single column; full-width inputs; touch targets ≥ 44px |
| Job create/edit | Wide form | Stacked fields; schedule picker usable without hover |
| Dashboard ops | Grid / multi-column | Single column; primary actions prominent |
| Settings | Form sections | Stacked; no side-by-side controls that clip |
| Login / setup | Centered card | Full-width card with comfortable padding |

### Touch & interaction

- Minimum **44×44px** tap targets for icon buttons, nav items, and row actions
- No hover-only affordances — expose actions via menus, visible buttons, or long-press where needed
- Dialogs and menus: max-height + scroll; avoid off-screen sheets on short viewports
- Form inputs: `16px` minimum font size on iOS to prevent zoom-on-focus (or accept zoom deliberately)

### Performance & polish

- Avoid layout shift when opening the nav drawer
- Tables/lists: preserve virtualization where already used; don't regress scroll on mobile
- Light/dark tokens unchanged — verify contrast on small screens

## Key files (expected)

- `frontend/src/components/layout/` — responsive shell, mobile nav drawer
- `frontend/src/components/ui/` — responsive variants for Table, Dialog, Sheet
- `frontend/src/pages/*` — per-page layout adjustments (especially Connections, RunDetail, Jobs)
- `frontend/tailwind.config.*` — breakpoint and spacing tokens if not already centralized
- `docs/architecture.md` — note responsive layout as a first-class UI concern

## Prerequisites

- [Phase 10](phase-10.md) — Radix + Tailwind stack and production layout shell (**required**)
- [Phase 14](phase-14.md) — dashboard, schedule picker, run export (**recommended** — exercises
  the heaviest ops views)
- [Phase 11](phase-11.md) — if TV job forms ship before this phase, include them in scope

## Defers to later phases

Nothing — last planned **product UI** phase.

## Out of scope

- Native iOS/Android apps or PWA install/offline support
- Backend or API changes
- TrueNAS / deployment changes
- Rewriting sync or connection logic

## Verification

Test plan TBD when phase lands — manual smoke on real devices or DevTools device emulation
(iPhone SE, iPhone 14, iPad portrait, ~390px and ~768px widths) across login, setup, connections,
jobs, runs, run detail + live logs, dashboard, settings. Vitest/RTL viewport tests where cheap;
no requirement for full visual regression tooling.

**Next:** [Phase index](README.md)
