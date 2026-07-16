# Phase 25 test plan — Ops & OSS hygiene

## Automated

- [x] `mise run check` passes (lint/mypy/tests; OpenAPI types regenerated)
- [x] Backend: backup download still works; restore accepts a valid snapshot and rejects garbage / missing tables / active run
- [x] Frontend: BackupSection restore confirm + success/failure toasts
- [x] Frontend: LiveStreamIndicator disconnected state; NotificationBell / useLogStream surface failures

## Manual

- [ ] Root `LICENSE` and `SECURITY.md` present and linked from README if applicable
- [ ] Dependabot config visible under repo Insights → Dependency graph → Dependabot
- [ ] Settings → Backup: download → restore same file → app still usable after reload
- [ ] Restore while a sync run is active is rejected with a clear error
- [ ] Open notification bell with API forced offline → error toast or inline message (not “No notifications yet”)
- [ ] Live run log stream: kill backend mid-stream → disconnected/error feedback (not silent)
