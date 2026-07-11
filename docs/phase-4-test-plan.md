# Phase 4 verification checklist

Jobs + runs + scheduler: full job CRUD, APScheduler manager/runner, run history API,
Jobs/Runs UI, and manual run via scheduler.

**Prerequisites:** [Phase 2](phase-2-test-plan.md) connections configured (all four services `ok`).
Shared setup: [testing.md](testing.md).

## What Phase 4 does *not* do yet

**Runs do not pull real Plex / Trakt / Letterboxd data.** Sources are still in-memory stubs
(`PlexSource`, `TraktSource`, `LetterboxdSource` wrap `MemorySource` with empty stores). The sync
engine and scheduler run end-to-end, but fetches return nothing until client-backed sources land in
[Phase 7](phase-7-test-plan.md).

What you *should* see in the UI:

- Job CRUD, scheduler registration, manual **Run now**, run history + detail
- Run finishes with status **success** (or **failed** if connections are missing)
- Summary counts are mostly **0** — that is expected, not a bug
- **Dry run** still matters for engine behavior (plans logged, no `apply_`* writes), but there is no
external data to sync either way
- **Live log viewer** and **notifications** arrive in Phases 5–6; run detail shows summary only



## 1. Automated tests

```bash
mise run test-backend    # tests/api/test_jobs.py, test_runs.py
mise run test-frontend   # App routing smoke
# or: mise run test
mise run check           # CI parity before marking phase done
```

Covers: job CRUD, manual run through scheduler, run list/detail API, scheduler registration on
create/update/delete.

## 2. UI walkthrough (browser)



### Setup

```bash
mise run up-dev          # recommended: hot reload at http://localhost:5173
# or: mise run up        # single container at http://localhost:8000
```

After wiping `./data`, skip the wizard if you have `.env` secrets:

```bash
mise run dev-bootstrap   # user + connections + cookies.txt
```

Sign in (or use bootstrap). Dashboard should show connection badges and no orange re-auth alert.

### Dashboard (`/`)

- [x] **API ✓** health badge and job count badge
- [x] Connection status badges for Plex, Trakt, Letterboxd, TMDB
- [x] **Sync jobs** section: enabled / dry-run counts (or link to create first job)
- [x] **Recent runs** section: empty until you run a job; links to run detail after a run
- [x] Header nav: **Jobs**, **Runs**, **Connections**



### Create a job (`/jobs/new`)

- [x] Click **New job** (from Jobs page or dashboard link)
- [x] Fill **Name** (e.g. `Plex ↔ Trakt test`)
- [x] **Source pair** — try each option; data-type checkboxes update per pair:
  - Plex ↔ Trakt → watchlist, watched history
  - Letterboxd → Plex → ratings only
  - Letterboxd → Trakt → ratings, watched history
- [x] Select at least one data type
- [x] **Cron schedule** — default `0 3` * * * (daily 03:00 UTC); edit to something valid
- [x] Toggle **Enabled** on, **Dry run** on (recommended for first test)
- [x] **Create job** → green toast, redirect to `/jobs`

Validation:

- [x] Submit with empty name → inline error
- [x] Uncheck all data types → inline error



### Jobs list (`/jobs`)

- [x] Table shows name, **Dry run** badge (when on), pair, data-type badges, cron, enabled/disabled
- [x] **▶ Run now** — button shows loading spinner; toast when finished (`Run #N finished with status success`)
- [x] **Edit** → `/jobs/:id/edit`
- [x] **History** → `/runs?job_id=:id`
- [x] **Delete** — confirm dialog, job removed from list



### Edit job (`/jobs/:id/edit`)

- [ ] Form pre-filled from existing job
- [ ] Change name, cron, dry-run, enabled, data types → **Save job** → back to list with updates
- [ ] Disable job → **Disabled** badge on list (scheduler drops cron; manual run still works)



### Run history (`/runs`)

- [ ] Table: run id (link), job name, trigger (`manual` / `scheduled`), status badge, dry-run badge,
  started time, duration
- [ ] Filter via **History** on a job row → title “Runs for job #N”, **All runs** link back
- [ ] Click run id → run detail



### Run detail (`/runs/:id`)

After **Run now** on a dry-run job:

- [ ] Status badge **success**, trigger **manual**, **dry run** badge
- [ ] Job name, started/finished timestamps
- [ ] **Summary** grid: Matched, Planned, Added, Removed, Rated, Watched, Skipped, Errors — expect
  **zeros** with current in-memory sources
- [x] Run detail shows summary and **Logs** panel (Phase 5)

Failure case (optional): stop one connection or wipe a connection row → **Run now** should show red
toast / run detail with **failed** and error mentioning missing connections.

### Scheduler (optional, slower)

- [x] Edit job cron to `* * * * *` (every minute), enabled, dry-run
- [x] Wait 1–2 minutes → **Runs** shows new row with trigger **scheduled**
- [x] Set cron back to a sane value when done



### Overlap lock (optional)

- [ ] Trigger **Run now** twice quickly on the same job — second request should not create a duplicate
  concurrent run (per-job lock; second may fail or skip depending on timing)



## 3. API smoke (optional)

```bash
mise run api-login
```

```bash
curl -s -b cookies.txt http://localhost:8000/api/jobs
curl -s -X POST http://localhost:8000/api/jobs \
  -H 'Content-Type: application/json' \
  -H 'X-Requested-With: XMLHttpRequest' \
  -b cookies.txt \
  -d '{"name":"Plex ↔ Trakt","source_pair":"plex_trakt","data_types":["watchlist"],"dry_run":true,"cron":"0 3 * * *","enabled":true}'
# → job JSON with id

curl -s -X POST http://localhost:8000/api/jobs/1/run \
  -H 'X-Requested-With: XMLHttpRequest' \
  -b cookies.txt
# → JobRunResponse: status success, summary counts 0

curl -s -b cookies.txt http://localhost:8000/api/runs
curl -s -b cookies.txt http://localhost:8000/api/runs/1
```



## 4. Scheduler notes

- Enabled jobs register a cron trigger on startup and on create/update.
- Manual **Run now** enqueues through APScheduler and blocks until the run completes.
- Per-job lock prevents overlapping executions (manual + scheduled).
- Connections must be `ok` for the job's source pair or the run fails fast with a clear error.
- Live log streaming and notifications arrive in Phases 5–6.



## 5. Reset

```bash
mise run down-v    # wipe ./data for fresh wizard + jobs
```

Then `mise run dev-bootstrap` if re-seeding from `.env`.
