# Phase 2 verification checklist

Connections + onboarding wizard: connection model with Fernet-encrypted secrets, four service
clients with `test_connection()`, Plex/Trakt/Letterboxd/TMDB setup steps, re-auth UI.

**Prerequisites:** [Phase 1](phase-1-test-plan.md) passing. Shared container setup: [testing.md](testing.md).

## 1. Automated tests

```bash
mise run test-backend    # tests/api/test_connections.py, tests/unit/test_security.py
mise run test-frontend   # frontend/src/App.test.tsx (connections gate)
# or: mise run test
mise run check           # CI parity before marking phase done
```

Covers: connection status endpoint, Fernet round-trip, TMDB/Plex/Letterboxd/Trakt save flows
(mocked HTTP), Trakt device OAuth poll, `needs_connections` gate, connections redirect.

## 2. Container — connections wizard

After Phase 1 user setup and login:

```bash
mise run up
```

Open http://localhost:5173 (Vite dev UI; API is proxied to :8000) and verify:

1. Sign in → redirected to `/connections` ("Connect your services")
2. Step through Plex → Trakt → Letterboxd → TMDB (use real credentials or test endpoints). Trakt env vars must be set in `.env` before the Trakt step.
3. Plex step shows authorization link + PIN code; polls until authorized and auto-discovers your server
4. Trakt step shows device code + verification URL; polls until authorized
4. After all four show `ok` status → lands on dashboard with connection badges
5. Dashboard "Manage connections" opens `/connections` for edits/re-auth
6. If Trakt status is `needs_reauth`, dashboard shows orange re-auth alert

## 3. API smoke (optional)

Create a session cookie jar first (see [testing.md](testing.md#api-smoke-sessions)):

```bash
mise run api-login
```

Then:

```bash
curl -s -b cookies.txt http://localhost:8000/api/connections/status
# → needs_connections true until all four services configured

curl -s -X POST http://localhost:8000/api/connections/tmdb/test \
  -H 'Content-Type: application/json' \
  -H 'X-Requested-With: XMLHttpRequest' \
  -b cookies.txt \
  -d '{"api_key":"your-key"}'
# → {"ok":true,...} or 400 with error detail
```

Secrets are never returned in API responses — only non-secret `config` fields and `status`.

## 4. Reset for re-testing

```bash
mise run down-v
mise run up
```

Re-run setup (Phase 1 user) then connections wizard. Local dev: `mise run clean-data && mise run db-upgrade`.

## 5. Notes

- Trakt uses a single server-level API app (`TRAKT_CLIENT_ID` / `TRAKT_CLIENT_SECRET` in `.env`). End users only authorize their Trakt account via device OAuth in the UI.
- Letterboxd is read-only; credentials are validated via login check (no write API).
- External HTTP calls are mocked in automated tests via `respx` / monkeypatch.
- Phase 3 sync engine will consume decrypted connection secrets from the service layer.
