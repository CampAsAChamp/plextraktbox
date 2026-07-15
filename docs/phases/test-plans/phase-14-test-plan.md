# Phase 14 verification checklist

**Scope:** Dashboard ops view, schedule presets / next-run display, clone job, run log export —
see [phase-14.md](../phase-14.md).

**Prerequisites:** Phases 0–8, 11–13, and 18 passing. Shared setup: [testing.md](../../testing.md).

## 1. Automated tests

```bash
mise run test-backend -- \
  tests/api/test_jobs.py \
  tests/api/test_run_logs.py
mise run test-frontend -- src/utils/cronPresets.test.ts
mise run check
```

- [ ] Job list/get includes `last_run` (null when never run; populated after a run)
- [ ] `POST /api/jobs/{id}/clone` copies config, appends `(copy)`, starts disabled
- [ ] Clone name collisions use `(copy 2)`, …
- [ ] `GET /api/runs/{id}/logs/export?format=txt|jsonl` returns attachment download
- [ ] Export 404 for unknown run
- [ ] Cron presets include Daily 3am, Every 6 hours, Weekly — all valid expressions

## 2. Container / browser

```bash
mise run up-dev   # or mise run dev-backend + mise run dev-frontend
```

- [ ] Dashboard shows each job with next run, last run status + matched/added/errors
- [ ] Failed/partial last runs appear in a red attention alert
- [ ] Dashboard **Run** and **Dry-run** start a run and toast the result
- [ ] Jobs table shows next-run text under the cron (not tooltip-only)
- [ ] Job form presets include **Every 6 hours**; selecting a preset fills cron and shows preview
- [ ] Jobs → **Clone** creates a disabled copy; edit/enable as needed
- [ ] Run detail → **Export** downloads `.txt` and `.jsonl`

## 3. API smoke (optional)

```bash
mise run api-login
curl -s -b cookies.txt http://localhost:8000/api/jobs | jq '.[0] | {name, next_run_at, last_run}'
# after creating a job with id=1:
curl -s -b cookies.txt -X POST -H 'X-Requested-With: XMLHttpRequest' \
  http://localhost:8000/api/jobs/1/clone | jq '{id, name, enabled}'
# after a run with id=1:
curl -s -b cookies.txt -o /tmp/run-1-logs.txt \
  'http://localhost:8000/api/runs/1/logs/export?format=txt'
head -5 /tmp/run-1-logs.txt
```

## 4. Reset / fixtures

```bash
# wipe local data and re-run setup wizard
rm -rf data/plextraktbox.db
mise run db-upgrade
```

## 5. Notes

- Cloned jobs start **disabled** so they do not fire on the schedule until reviewed.
- Dashboard dry-run forces `dry_run=true`; plain Run follows job + global dry-run resolution.
- Log export materializes the full run (paginated under the hood); fine for typical self-hosted
  volume.
