# Phase 20 — Mobile & responsive layout

**Status:** Done

## Goal

Make the full SPA usable on phones and small tablets — not a separate mobile app, but a responsive
layout that preserves every flow from desktop. Dense layouts on large screens; readable,
touch-friendly layouts below ~768px.

**No new sync features or API endpoints.**

## Context

The app is built for repeat desktop use (header nav, wide tables, split-pane run detail). Viewport meta
is already set; the gap is layout, navigation, and component behavior at narrow widths. Do this **after**
major UX flows ([Phase 14](phase-14.md)) so responsive work targets the production Mantine pages.

## Deliverables

### Layout shell

- **Breakpoint strategy** — use Mantine breakpoints (`sm` / `md` / `lg`); default
  mobile-first where practical
- **Nav → drawer / stacked** — header links become a hamburger or equivalent on small viewports;
  focus trap + escape to close when using a drawer
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

- `frontend/src/components/layout/` — responsive shell / mobile nav if introduced
- `frontend/src/pages/*` — per-page layout adjustments (especially Connections, RunDetail, Jobs)
- Mantine responsive props / CSS modules as needed
- `docs/architecture.md` — note responsive layout as a first-class UI concern

## Prerequisites

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

See [test-plans/phase-20-test-plan.md](test-plans/phase-20-test-plan.md) — manual smoke at ~390px /
~768px across login, setup, connections, jobs, runs, run detail + live logs, dashboard, settings;
AppLayout drawer vitest coverage.

**Next:** [Phase index](README.md) · [Phase 21](phase-21.md) (sync caches)
