# Phase 14 — Dashboard & scheduling UX

**Status:** Done

## Goal

Make day-to-day operation pleasant: see job health at a glance, pick schedules without writing cron
by hand, and export run logs for debugging.

## Deliverables

### Dashboard ops view

- Per-job **last run** status + summary counts (matched/added/errors) — `last_run` on job API
- Failure/partial run alerts surfaced prominently
- Quick **Run** and **Dry-run** actions from dashboard

### Scheduling UX

- **Next scheduled run** — APScheduler next-fire-time API; display in user's timezone on Jobs +
  Dashboard
- **Friendly schedule picker** — presets ("Daily 3am", "Every 6 hours", "Weekly") → cron; advanced
  raw cron still available
- **Cron preview in local time** — show next N run times under the cron field

### Job & run utilities

- **Clone job** — `POST /api/jobs/{id}/clone` duplicates config (starts disabled)
- **Export run logs** — download `.txt` or `.jsonl` from run detail

## Key files

- `backend/plextraktbox/api/jobs.py` — `last_run`, clone, next-run on responses
- `backend/plextraktbox/api/run_logs.py` — log export
- `frontend/src/pages/Dashboard/` — ops view
- `frontend/src/components/JobForm/` — schedule picker + cron preview
- `frontend/src/pages/RunDetailPage.tsx` — export menu
- `frontend/src/pages/JobsPage.tsx` — next-run text, clone action

## Prerequisites

[Phase 13](phase-13.md) — settings and safety rails in place

## Defers to later phases

| Item | Phase |
| ---- | ----- |
| Mobile & responsive layout (sidebar drawer, tables, split panes) | 20 |

## Verification

[phase-14-test-plan.md](test-plans/phase-14-test-plan.md)

**Next:** [Phase 15 — Doppler secrets](phase-15.md) (done) or
[Phase 20 — Mobile layout](phase-20.md) / [Phase 19 — Automated releases](phase-19.md)
