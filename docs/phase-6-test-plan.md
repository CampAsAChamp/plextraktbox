# Phase 6 verification checklist

**Scope:** Notifications — config model + CRUD UI, dispatcher, Discord/in-app channels,
per-job override + global settings, test buttons, in-app bell.

**Prerequisites:** [Phase 5](phase-5-test-plan.md) logging pipeline passing. Shared setup:
[testing.md](testing.md).

## What Phase 6 adds

- `notification_config` and `inapp_notification` tables (+ job `notify_override_json`)
- Dispatcher fan-out on run finalize (Discord webhook, in-app row)
- Settings → **Notifications** for global channel config + test buttons
- Navbar **bell** with unread count, mark read, links to runs
- Job form **Notifications** mode: inherit global / custom per-job / disabled

## 1. Automated tests

```bash
mise run test-backend    # tests/unit/test_notifications_dispatcher.py, tests/api/test_notifications.py
mise run test-frontend
# or: mise run test
mise run check           # CI parity before marking phase done
```

- [ ] `test_notifications_dispatcher.py` — resolve configs, in-app insert, Discord webhook
- [ ] `test_notifications_api.py` — CRUD auth, in-app test + read/mark-all, Discord test

## 2. Container / browser

```bash
mise run up-dev          # recommended: http://localhost:5173
# or: mise run up        # http://localhost:8000
mise run db-upgrade      # applies notification migrations
```

After bootstrap (`mise run dev-bootstrap` if needed):

- [ ] **Settings → Notifications** — enable in-app, save, click **Send test**
- [ ] Bell icon shows unread badge; open menu → test notification appears
- [ ] Click notification (or **Mark all read**) — badge clears
- [ ] Optional: configure Discord webhook and send test
- [ ] Create/edit job → set notification mode; run job → in-app alert on completion

## 3. API smoke

```bash
mise run api-login
curl -s -b cookies.txt http://localhost:8000/api/notifications/configs | jq .
curl -s -b cookies.txt http://localhost:8000/api/notifications/inapp/unread-count | jq .
```

## 4. Reset / fixtures

```bash
mise run down-v && mise run up-dev
mise run dev-bootstrap
```

## 5. Notes

- Discord tests use `respx` mocks; no live webhook required in CI
- Notification failures log warnings and never fail the sync run
- Per-job **custom** mode uses job-scoped configs (`scope=job`); configure via API today (UI in Settings is global-only)
