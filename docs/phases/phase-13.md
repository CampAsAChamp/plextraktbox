# Phase 13 — Settings, safety & operations

**Status:** Done

## Goal

Global app settings, safety rails around live sync, and operational health/backup tooling so the app
is safe to run unattended on a home server.

## Deliverables

### Settings model + UI

- **`setting` table** + Settings page (Mantine)
- Default cron expression
- **Cron timezone** — Local / UTC / Manual (IANA), same modes as display prefs, for interpreting job cron hour/minute fields
- `log_retention_days`
- **Global dry-run default** — seeds new jobs; runner resolves `override ?? job.dry_run`
- **Password change** in Settings
- Gravatar/settings profile polish

### Safety guards

- **First run must be dry-run** — per-job `require_dry_run_first` coerces live runs to dry-run until
  ≥1 successful dry-run exists for that job
- **Exclude/ignore list** — global TMDB/IMDb/TVDB ids in settings; optional per-job override via
  `exclude_ids_json` (union with global)

### Connection health

- Scheduled `test_connection()` job (every 6h)
- Update connection `status` on failure/expiry
- Notification when status becomes `needs_reauth`

### Operations

- **Log retention** — scheduled job prunes old `log_entry` / `job_run` rows per `log_retention_days`
- **Richer `/api/health`** — scheduler alive, DB writable, connection status summary (version/build
  identity is [Phase 18](phase-18.md))
- **SQLite backup** — Settings download button + note for ZFS snapshots of `/data`

## Key files

- `backend/plextraktbox/models/setting.py`, `api/settings.py`, `api/health.py`
- `backend/plextraktbox/scheduler/system_jobs.py` — retention + connection health
- `frontend/src/pages/Settings/`

## Prerequisites

[Phase 8](phase-8.md) — real movie sync proven; [Phase 11](phase-11.md) if TV is in scope

## Defers to later phases

| Item | Phase |
| ---- | ----- |
| Dashboard ops view, friendly cron picker | 14 |
| Log export download | 14 |
| Doppler maintainer workflow | 15 |
| Sync cache TTL / clear-cache UI (LB, Trakt, Discover — caches themselves) | 21 |
| TrueNAS deploy docs | 22 |
| UI themes (built-ins + custom upload/volume) | 24 |

## Verification

[phase-13-test-plan.md](test-plans/phase-13-test-plan.md)

**Next:** [Phase 14 — Dashboard & scheduling UX](phase-14.md)
