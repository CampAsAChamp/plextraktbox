# Phase 12 — Settings, safety & operations

**Status:** Planned

## Goal

Global app settings, safety rails around live sync, operational health/backup tooling, and CI so the
app is safe to run unattended on a home server.

## Deliverables

### Settings model + UI

- **`setting` table** + Settings page (on [Phase 10](phase-10.md) UI stack)
- Default cron expression
- `log_retention_days`
- **Global dry-run default** — runner resolves `override ?? job.dry_run ?? global`

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
- **Richer `/api/health`** — version, scheduler alive, DB writable, connection status summary
- **SQLite backup** — Settings download button + README note for ZFS snapshots
- **Password change** in Settings

### Quality & DX

- structlog redaction audit; improve error surfaces in API/UI
- **GitHub Actions CI** — restore `.github/workflows/ci.yml`, mirror `mise run check`
- OpenAPI → TypeScript types generation
- e2e smoke test
- Gravatar/settings profile polish

## Key files (expected)

- `backend/plextraktbox/models/setting.py`, `api/settings.py`, `api/health.py`
- `backend/plextraktbox/scheduler/` — retention + health jobs
- `frontend/src/pages/Settings/`
- `.github/workflows/ci.yml`

## Prerequisites

[Phase 8](phase-8.md) — real movie sync proven; [Phase 10](phase-10.md) UI stack; [Phase 11](phase-11.md)
if TV is in scope

## Defers to later phases

| Item | Phase |
| ---- | ----- |
| Dashboard ops view, friendly cron picker | 13 |
| Log export download | 13 |
| Doppler maintainer workflow | 14 |
| TrueNAS deploy docs | 15 |

## Verification

Test plan TBD when phase lands — copy [phase-test-plan-template.md](test-plans/phase-test-plan-template.md).

**Next:** [Phase 13 — Dashboard & scheduling UX](phase-13.md)
