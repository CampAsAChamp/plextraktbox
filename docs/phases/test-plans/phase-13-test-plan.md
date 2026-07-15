# Phase 13 verification checklist

**Scope:** Settings, dry-run safety, exclude lists, connection health cron, log retention, richer
health, SQLite backup — see [phase-13.md](../phase-13.md).

**Prerequisites:** Phases 0–8, 11, 12, and 18 passing. Shared setup: [testing.md](../../testing.md).

## 1. Automated tests

```bash
mise run test-backend -- \
  tests/api/test_settings.py \
  tests/api/test_change_password.py \
  tests/api/test_health.py \
  tests/unit/test_settings_service.py \
  tests/unit/test_dry_run_guards.py \
  tests/unit/test_retention.py \
  tests/unit/test_connection_health_job.py
mise run check
```

- [ ] Settings GET seeds defaults; PUT validates cron / retention
- [ ] Password change updates hash; wrong current rejected
- [ ] `require_dry_run_first` coerces live runs until a successful dry-run exists
- [ ] Exclude filter drops TMDB/IMDb/TVDB matches in `SyncContext.fetch`
- [ ] Retention deletes old completed runs + logs; keeps running / recent
- [ ] Connection health notifies once on transition into `needs_reauth`
- [ ] `/api/health` returns `ok` / `degraded` with db, scheduler, connections
- [ ] Backup download returns SQLite file bytes

## 2. Container / browser

```bash
mise run up-dev   # or mise run dev-backend + mise run dev-frontend
```

- [ ] Settings → Account: change password, then log in with the new password
- [ ] Settings → Sync defaults: toggle global dry-run, set cron timezone (UTC vs local) / cron / retention / excludes, save
- [ ] Create a new job — cron and dry-run match Settings defaults; require dry-run first is on
- [ ] Run a new job live — run is coerced to dry-run until a successful dry-run completes
- [ ] Settings → Download database backup produces `plextraktbox-backup.db`
- [ ] Header health badge stays green when healthy; yellow when a connection is `needs_reauth`

## 3. API smoke (optional)

```bash
mise run api-login
curl -s -b cookies.txt http://localhost:8000/api/settings | jq .
curl -s -b cookies.txt -o /tmp/plextraktbox-backup.db http://localhost:8000/api/settings/backup
file /tmp/plextraktbox-backup.db
curl -s http://localhost:8000/api/health | jq .
```

## 4. Reset / fixtures

```bash
# wipe local data and re-run setup wizard
rm -rf data/plextraktbox.db
mise run db-upgrade   # if using an existing DATA_DIR
```

## 5. Notes

- Prefer ZFS snapshots of the `/data` mount on TrueNAS for routine backups; Settings backup is for
  ad-hoc downloads.
- Global dry-run seeds **new** jobs only; existing jobs keep their stored `dry_run` flag.
- Connection health runs every 6h (`system_connection_health`); retention daily at 04:15 UTC.
