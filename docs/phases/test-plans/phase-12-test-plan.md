# Phase 12 verification checklist

**Scope:** GitHub Actions CI, structlog redaction, API error surfacing, OpenAPI→TS types, API smoke
— see [phase-12.md](../phase-12.md).

**Prerequisites:** Phases 0–8, 11, 18 passing. Shared setup: [testing.md](../../testing.md).

## 1. Automated tests

```bash
mise run test-backend   # includes tests/api/test_smoke.py + unit/test_logstream.py
mise run test-frontend  # includes api/client.test.ts + health.test.ts
mise run check          # lint + OpenAPI drift check + all tests (CI parity)
```

- [ ] `test_smoke_health_login_list_jobs` passes (in-process TestClient, throwaway SQLite)
- [ ] Redaction tests cover nested keys, extended patterns, and `redact_log_processor` mutation
- [ ] `formatApiDetail` formats 422 validation arrays
- [ ] `mise run check-api-types` clean after `mise run generate-api-types`
- [ ] `health.ts` types come from `frontend/src/api/generated/schema.d.ts`

## 2. Container / browser

```bash
mise run up   # optional — not required for this phase’s CI/smoke path
```

- [ ] Local `mise run check` matches what GitHub Actions will run
- [ ] Pushing a PR triggers the `CI` workflow (`.github/workflows/ci.yml`)

## 3. API smoke (optional live)

In-process smoke is covered by pytest. For a live container session:

```bash
mise run api-login   # writes cookies.txt — see testing.md
curl -s -b cookies.txt http://localhost:8000/api/jobs
```

## 4. Reset / fixtures

```bash
# pytest uses a fresh SQLite per test (tmp_path) — no reset needed
# After regenerating OpenAPI types:
mise run generate-api-types
# commit frontend/src/api/generated/schema.d.ts when the schema changes
```

## 5. Notes

- CI stubs `.env` with dummy `SECRET_KEY` / Trakt placeholders; no real service credentials.
- API smoke is **not** Playwright — it runs inside pytest against `create_app()`.
- OpenAPI codegen uses in-process `create_app().openapi()` (no running server).
