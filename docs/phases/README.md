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
| 7 | [Client-backed sources (movies)](phase-7.md) | **Next** | Real Plex/Trakt/LB fetch + apply | [phase-7](test-plans/phase-7-test-plan.md) |
| 8 | [Settings & operations](phase-8.md) | Planned | Safety guards, health, backup, CI | TBD |
| 9 | [Dashboard & scheduling UX](phase-9.md) | Planned | Ops view, schedule picker, export | TBD |
| 10 | [TV sync](phase-10.md) | Planned | Shows and episodes | TBD |
| 11 | [TrueNAS install](phase-11.md) | Planned | Personal box, GHCR, TLS docs | TBD |
| 12 | [TrueNAS catalog](phase-12.md) | Planned | App catalog publication | TBD |
| 13 | [Doppler secrets](phase-13.md) | Planned | Maintainer dev/CI workflow | TBD |
| 14 | [UI polish](phase-14.md) | Planned | Visual/layout pass | TBD |

**Current focus:** Phase 7 — wire sources to real APIs for movies; Phases 0–6 are complete.

When a phase lands: update its scope doc (mark done), copy
[test-plans/phase-test-plan-template.md](test-plans/phase-test-plan-template.md) →
`test-plans/phase-N-test-plan.md`, and update **this table** (the single source of truth for progress).
