# Phase 10 — Dashboard & scheduling UX

**Status:** Planned

## Goal

Make day-to-day operation pleasant: see job health at a glance, pick schedules without writing cron
by hand, and export run logs for debugging.

## Deliverables

### Dashboard ops view

- Per-job **last run** status + summary counts (matched/added/errors)
- Failure/partial run alerts surfaced prominently
- Quick **Run** and **Dry-run** actions from dashboard

### Scheduling UX

- **Next scheduled run** — APScheduler next-fire-time API; display in user's timezone on Jobs +
  Dashboard
- **Friendly schedule picker** — presets ("Daily 3am", "Every 6 hours") → cron; advanced raw cron
  still available
- **Cron preview in local time** — show next N run times under the cron field

### Job & run utilities

- **Clone job** — duplicate config to a new job
- **Export run logs** — download `.txt` or `.jsonl` from run detail

## Key files (expected)

- `backend/plextraktbox/api/jobs.py` — next-run endpoint
- `frontend/src/pages/Dashboard/`, `components/JobForm/` (schedule picker)
- `frontend/src/pages/RunDetail/` (export button)

## Prerequisites

[Phase 9](phase-9.md) — settings and safety rails in place

## Defers to later phases

| Item | Phase |
| ---- | ----- |
| Visual/layout polish | 15 |

## Verification

Test plan TBD when phase lands.

**Next:** [Phase 11 — TV sync](phase-11.md)
