# Phase index

plextraktbox is built incrementally — each phase is independently runnable and testable. This
directory holds **scope docs** (`phase-N.md`) and **verification checklists** ([test-plans/](test-plans/)).

Architecture and locked decisions: [architecture.md](../architecture.md). How to run checks:
[testing.md](../testing.md). Dev ergonomics: [dev-workflow.md](../dev-workflow.md).

## Progress

| Phase | Name | Status | Scope | Test plan |
| ----- | ---- | ------ | ----- | --------- |
| 0 | [Scaffold](phase-0.md) | Done | Docker, DB, health, SPA shell | [phase-0](test-plans/phase-0-test-plan.md) |
| 1 | [Auth + wizard](phase-1.md) | Done | Single user, sessions, setup gate | [phase-1](test-plans/phase-1-test-plan.md) |
| 2 | [Connections](phase-2.md) | Done | Plex/Trakt/LB/TMDB onboarding | [phase-2](test-plans/phase-2-test-plan.md) |
| 3 | [Sync engine core](phase-3.md) | Done | Matching, reconcilers, dry-run | [phase-3](test-plans/phase-3-test-plan.md) |
| 4 | [Jobs + scheduler](phase-4.md) | Done | Job CRUD, APScheduler, run history | [phase-4](test-plans/phase-4-test-plan.md) |
| 5 | [Logging + live viewer](phase-5.md) | Done | structlog, SSE, LogViewer | [phase-5](test-plans/phase-5-test-plan.md) |
| 6 | [Notifications](phase-6.md) | Done | Discord, in-app bell | [phase-6](test-plans/phase-6-test-plan.md) |
| 7 | [Client-backed fetch (movies)](phase-7.md) | Done | Real Plex/Trakt/LB fetch | [phase-7](test-plans/phase-7-test-plan.md) |
| 8 | [Client-backed apply (movies)](phase-8.md) | **Next** | Real Plex/Trakt apply | [phase-8](test-plans/phase-8-test-plan.md) |
| 9 | [Frontend prototype](phase-9.md) | Planned | Run detail + log viewer spike | TBD |
| 10 | [Frontend redesign](phase-10.md) | Planned | Full Radix + Tailwind migration | TBD |
| 11 | [TV sync](phase-11.md) | Planned | Shows and episodes | TBD |
| 12 | [CI & quality](phase-12.md) | Planned | GitHub Actions, e2e, API types | TBD |
| 13 | [Settings & operations](phase-13.md) | Planned | Safety guards, health, backup | TBD |
| 14 | [Dashboard & scheduling UX](phase-14.md) | Planned | Ops view, schedule picker, export | TBD |
| 15 | [Doppler secrets](phase-15.md) | Planned | Maintainer dev/CI workflow | TBD |
| 16 | [TrueNAS install](phase-16.md) | Planned | Personal box, GHCR, TLS docs | TBD |
| 17 | [TrueNAS catalog](phase-17.md) | Planned | App catalog publication | TBD |
| 18 | [Version & build info](phase-18.md) | Done | Running version in UI, build metadata | [phase-18](test-plans/phase-18-test-plan.md) |
| 19 | [Automated releases](phase-19.md) | Planned | release-please, GHCR, semver bumps | [phase-19](test-plans/phase-19-test-plan.md) |

**Current focus:** Phase 8 — wire source **apply** to real APIs for movies; Phases 0–7 and 18 are complete.

## Delivery order

Phase numbers follow implementation order where possible. [Phase 18](phase-18.md) shipped early;
use the tracks below when parallel work makes sense.

```
Product (primary)     7 ✓ → 8 → 9–11 (as needed) → 13 → 14

Release / deploy      18 ✓ → 12 → 19 → 16 → 17

Maintainer (optional) 15 — Doppler; anytime for dev/CI secrets
```

| Track | Order | Notes |
| ----- | ----- | ----- |
| **Product** | 8 | Real movie apply completes the sync milestone |
| **Product** | 9 → 10, 11 | UI spike/redesign and TV can overlap 7–8 or follow |
| **Ops** | 13 → 14 | Settings/safety, then dashboard UX — after core sync works |
| **Release** | 12 → **19** → **16** → 17 | CI before automated releases; GHCR before TrueNAS install |
| **Maintainer** | 15 | Independent of deploy |

When a phase lands: update its scope doc (mark done), copy
[test-plans/phase-test-plan-template.md](test-plans/phase-test-plan-template.md) →
`test-plans/phase-N-test-plan.md`, and update **this table** (the single source of truth for progress).
