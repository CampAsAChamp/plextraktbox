# Phase 5 verification checklist

**Scope:** Logging pipeline + live viewer — structlog run log persistence, SSE streaming,
LogViewer with auto-scroll, filters, and virtualization.

**Prerequisites:** [Phase 4](phase-4-test-plan.md) jobs + scheduler passing. Shared setup:
[testing.md](testing.md).

## What Phase 5 adds

- Per-run structlog lines persisted to `log_entry` and published to an in-process pub/sub channel
- `GET /api/runs/{id}/logs` for historical paging/filtering
- `GET /api/runs/{id}/logs/stream` (SSE) for live + replay on connect
- Run detail page embeds **LogViewer** (level filter, search, stick-to-bottom, jump-to-latest)

## 1. Automated tests

```bash
mise run test-backend    # tests/unit/test_logstream.py, tests/api/test_run_logs.py
mise run test-frontend
# or: mise run test
mise run check           # CI parity before marking phase done
```

- [ ] `test_logstream.py` — redaction, pub/sub backlog/close
- [ ] `test_run_logs.py` — REST list after job run, SSE end event on completed run

## 2. Container / browser

```bash
mise run up-dev          # recommended: http://localhost:5173
# or: mise run up        # http://localhost:8000
mise run db-upgrade      # applies 005_log_entry migration
```

After bootstrap (`mise run dev-bootstrap` if needed):

- [ ] Create or use an existing job; click **Run now**
- [ ] Open **Run history** → run detail
- [ ] **Logs** panel shows lines including `sync.run.complete`
- [ ] Level filter and search narrow visible lines
- [ ] Scroll up → **Jump to latest** pill appears; click returns to bottom
- [ ] Completed runs load historical logs via REST (refresh page — lines remain)

## 3. API smoke

```bash
mise run api-login
RUN_ID=1   # replace with a real run id
curl -s -b cookies.txt "http://localhost:8000/api/runs/$RUN_ID/logs" | jq '.items | length'
curl -N -b cookies.txt "http://localhost:8000/api/runs/$RUN_ID/logs/stream"
```

Expect JSON log items and an SSE stream ending with `{"type":"end","status":"..."}`.

## 4. Reset / fixtures

```bash
mise run down-v && mise run up-dev
mise run dev-bootstrap
```

## 5. Notes

- Manual **Run now** blocks until the job finishes. With `SYNC_RUN_DELAY_SECONDS=10` in `.env`
  (dev only), runs stay `running` long enough to open the run detail page and watch live logs.
- Sensitive context keys (`token`, `password`, `secret`, etc.) are redacted before persist/stream.
- Full log retention pruning arrives in Phase 7.
