# Phase 4 — Jobs + runs + scheduler

**Status:** Done

## Goal

Persist sync jobs, run them on a cron schedule or on demand via APScheduler, and expose run history
in the API and UI — still using in-memory source stubs until Phase 7.

## Deliverables

- **job** model — name, `source_pair`, enabled, cron, `dry_run`, `data_types_json`, optional
  notify/exclude overrides
- **job_run** model — trigger (scheduled|manual), status, `summary_json`, timestamps
- Jobs CRUD API + **JobForm** UI
- **scheduler/manager.py** — `AsyncIOScheduler` + `SQLAlchemyJobStore`; `sync_job()` on CRUD;
  `max_instances=1`, `coalesce=True`
- **scheduler/runner.py** — single entry for all runs: create JobRun → bind logger → `engine.run` →
  finalize
- **Run now:** `POST /api/jobs/{id}/run` schedules immediate execution
- Run history list + detail pages (summary only until Phase 5 logs)

## Key files

- `backend/plextraktbox/models/job.py`, `job_run.py`, `scheduler/`, `api/jobs.py`, `api/runs.py`
- `frontend/src/pages/Jobs`, `RunHistory`, `RunDetail`, `components/JobForm/`

## Prerequisites

[Phase 3](phase-3.md)

## Important limitation (until Phase 7)

Sources wrap **MemorySource** with empty stores — runs complete successfully but summary counts are
mostly **zero**. This is expected, not a bug. Dry-run behavior and scheduler wiring are what Phase 4
proves.

## Defers to later phases

- Live log streaming on run detail (Phase 5)
- Notifications on run complete (Phase 6)
- Real Plex/Trakt/Letterboxd data (Phase 7)

## Verification

[phase-4-test-plan.md](test-plans/phase-4-test-plan.md)

**Next:** [Phase 5 — Logging + live viewer](phase-5.md)
