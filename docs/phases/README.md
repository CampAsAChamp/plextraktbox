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
| 8 | [Client-backed apply (movies)](phase-8.md) | Done | Real Plex/Trakt apply | [phase-8](test-plans/phase-8-test-plan.md) |
| 11 | [TV sync](phase-11.md) | Done | Shows and episodes | [phase-11](test-plans/phase-11-test-plan.md) |
| 12 | [CI & quality](phase-12.md) | Planned | GitHub Actions, e2e, API types | TBD |
| 13 | [Settings & operations](phase-13.md) | Planned | Safety guards, health, backup | TBD |
| 14 | [Dashboard & scheduling UX](phase-14.md) | Planned | Ops view, schedule picker, export | TBD |
| 15 | [Doppler secrets](phase-15.md) | Planned | Maintainer dev/CI workflow | TBD |
| 18 | [Version & build info](phase-18.md) | Done | Running version in UI, build metadata | [phase-18](test-plans/phase-18-test-plan.md) |
| 19 | [Automated releases](phase-19.md) | Planned | release-please, GHCR, semver bumps | [phase-19](test-plans/phase-19-test-plan.md) |
| 20 | [Mobile & responsive layout](phase-20.md) | Planned | Phone/tablet layouts, touch UX | TBD |
| 21 | [Sync fetch & resolve caches](phase-21.md) | Planned | LB/Trakt/Discover caches + once-per-run Plex library | TBD |
| 22 | [TrueNAS install](phase-22.md) | Planned | Personal box, GHCR, TLS docs | TBD |
| 23 | [TrueNAS catalog](phase-23.md) | Planned | App catalog publication | TBD |
| 24 | [UI themes](phase-24.md) | Planned | Built-ins + custom upload/volume | TBD |

**Current focus:** Phase 12 or product track Phase 13; Phases 0–8, 11, and 18 are complete.

Phases **9–10** (frontend prototype / redesign) were retired — stay on Mantine. Phases 16–17 were
retired (TrueNAS moved to **22–23**). [Phase 24](phase-24.md) (UI themes) is last on the roadmap;
can ship anytime after Phase 13.

## Delivery order

Phase numbers follow implementation order where possible. [Phase 18](phase-18.md) shipped early;
use the tracks below when parallel work makes sense.

```
Product (primary)     7 ✓ → 8 ✓ → 11 ✓ → 13 → 14 → 20
Sync performance      21 — anytime after 8 (LB/Trakt/Discover caches + Plex once-per-run)

Release                18 ✓ → 12 → 19

TrueNAS                22 → 23 — after product + GHCR releases

Themes (last)          24 — after TrueNAS (or anytime after 13)

Maintainer (optional)  15 — Doppler; anytime for dev/CI secrets
```

| Track | Order | Notes |
| ----- | ----- | ----- |
| **Product** | **13** | Settings after TV sync |
| **Sync perf** | **21** | Independent of UI; do when sync fetches/resolve dominate runtime |
| **Ops** | 13 → 14 → **20** | Settings/safety, dashboard UX, then mobile — after core sync |
| **Release** | 12 → **19** | CI before automated releases / GHCR |
| **TrueNAS** | **22** → **23** | Personal install then catalog; needs GHCR from 19 |
| **Themes** | **24** | After TrueNAS (or anytime after 13); Mantine palettes + custom CSS |
| **Maintainer** | 15 | Independent of deploy |

When a phase lands: update its scope doc (mark done), copy
[test-plans/phase-test-plan-template.md](test-plans/phase-test-plan-template.md) →
`test-plans/phase-N-test-plan.md`, and update **this table** (the single source of truth for progress).
