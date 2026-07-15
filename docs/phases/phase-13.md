# Phase 13 — Settings, safety & operations

**Status:** Planned

## Goal

Global app settings, safety rails around live sync, and operational health/backup tooling so the app
is safe to run unattended on a home server.

## Deliverables

### Settings model + UI

- **`setting` table** + Settings page (on [Phase 10](phase-10.md) UI stack)
- Default cron expression
- `log_retention_days`
- **Global dry-run default** — runner resolves `override ?? job.dry_run ?? global`
- **Password change** in Settings
- Gravatar/settings profile polish

### Safety guards

- **First run must be dry-run** — per-job `require_dry_run_first` blocks live apply until ≥1
  successful dry-run exists for that job
- **Exclude/ignore list** — global TMDB/IMDb ids in settings; optional per-job override via
  `exclude_ids_json`

### Connection health

- Scheduled `test_connection()` job
- Update connection `status` on failure/expiry
- Optional notification when status becomes `needs_reauth`

### Operations

- **Log retention** — scheduled job prunes old `log_entry` / `job_run` rows per `log_retention_days`
- **Richer `/api/health`** — scheduler alive, DB writable, connection status summary (version/build
  identity is [Phase 18](phase-18.md))
- **SQLite backup** — Settings download button + README note for ZFS snapshots

## Key files (expected)

- `backend/plextraktbox/models/setting.py`, `api/settings.py`, `api/health.py`
- `backend/plextraktbox/scheduler/` — retention + health jobs
- `frontend/src/pages/Settings/`

## Prerequisites

[Phase 8](phase-8.md) — real movie sync proven; [Phase 10](phase-10.md) UI stack; [Phase 11](phase-11.md)
if TV is in scope

## Defers to later phases

| Item | Phase |
| ---- | ----- |
| Dashboard ops view, friendly cron picker | 14 |
| Log export download | 14 |
| Doppler maintainer workflow | 15 |
| TrueNAS deploy docs | 16 |
| Sync cache TTL / clear-cache UI (LB, Trakt, Discover — caches themselves) | 21 |

## Verification

Test plan TBD when phase lands — copy [phase-test-plan-template.md](test-plans/phase-test-plan-template.md).

**Next:** [Phase 14 — Dashboard & scheduling UX](phase-14.md)
