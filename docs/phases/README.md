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
| 12 | [CI & quality](phase-12.md) | Done | GitHub Actions, e2e, API types | [phase-12](test-plans/phase-12-test-plan.md) |
| 13 | [Settings & operations](phase-13.md) | Done | Safety guards, health, backup | [phase-13](test-plans/phase-13-test-plan.md) |
| 14 | [Dashboard & scheduling UX](phase-14.md) | Done | Ops view, schedule picker, export | [phase-14](test-plans/phase-14-test-plan.md) |
| 15 | [Doppler secrets](phase-15.md) | Done | Maintainer dev/CI workflow | [phase-15](test-plans/phase-15-test-plan.md) |
| 18 | [Version & build info](phase-18.md) | Done | Running version in UI, build metadata | [phase-18](test-plans/phase-18-test-plan.md) |
| 19 | [Automated releases](phase-19.md) | Done | semantic-release, GHCR, semver bumps | [phase-19](test-plans/phase-19-test-plan.md) |
| 20 | [Mobile & responsive layout](phase-20.md) | Done | Phone/tablet layouts, touch UX | [phase-20](test-plans/phase-20-test-plan.md) |
| 21 | [Sync fetch & resolve caches](phase-21.md) | Done | LB/Trakt/Discover caches + once-per-run Plex library | [phase-21](test-plans/phase-21-test-plan.md) |
| 22 | [TrueNAS install](phase-22.md) | Done | Personal box, GHCR, Cloudflare Tunnel | [phase-22](test-plans/phase-22-test-plan.md) |
| 23 | [TrueNAS catalog](phase-23.md) | Planned | App catalog publication | TBD |
| 24 | [UI themes](phase-24.md) | Done | Built-ins + custom upload/volume | [phase-24](test-plans/phase-24-test-plan.md) |

**Current focus:** TrueNAS catalog ([Phase 23](phase-23.md)); Phases 0–8, 11–15, 18–22, and **24**
are complete.

Phases **9–10** (frontend prototype / redesign) were retired — stay on Mantine. Phases 16–17 were
retired (TrueNAS moved to **22–23**). [Phase 24](phase-24.md) (UI themes) is done — factory default
is Atom One Dark Pro. [Phase 21](phase-21.md) (sync caches) is done. [Phase 22](phase-22.md)
(personal TrueNAS install) is done.

## Delivery order

Phase numbers follow implementation order where possible. [Phase 18](phase-18.md) shipped early;
use the tracks below when parallel work makes sense.

```
Product (primary)     7 ✓ → 8 ✓ → 11 ✓ → 13 ✓ → 14 ✓ → 20 ✓
Sync performance      21 ✓ — LB/Trakt/Discover caches + Plex once-per-run

Release                18 ✓ → 12 ✓ → 19 ✓

TrueNAS                22 ✓ → 23 — personal install done; catalog next

Themes (last)          24 ✓ — Atom One Dark Pro default + custom upload/volume

Maintainer (optional)  15 ✓ — Doppler
```

| Track | Order | Notes |
| ----- | ----- | ----- |
| **Product** | 14 ✓ → 20 ✓ | Dashboard + mobile done |
| **Sync perf** | **21** ✓ | LB export/slug, Trakt lists, Discover keys, Plex once-per-run |
| **Ops** | 13 ✓ → 14 ✓ → 20 ✓ | Settings + dashboard + mobile done |
| **Release** | 12 ✓ → 19 ✓ | CI + automated releases / GHCR done |
| **TrueNAS** | 22 ✓ → **23** | Personal install done; catalog next |
| **Themes** | **24** ✓ | Mantine palettes + custom CSS; default Atom One Dark Pro |
| **Maintainer** | 15 ✓ | Doppler optional for local/CI secrets |

When a phase lands: update its scope doc (mark done), copy
[test-plans/phase-test-plan-template.md](test-plans/phase-test-plan-template.md) →
`test-plans/phase-N-test-plan.md`, and update **this table** (the single source of truth for progress).
