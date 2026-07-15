# Phase 12 — CI & quality

**Status:** Done

## Goal

Restore automated checks in GitHub Actions and tighten quality gates so releases and day-to-day
development share the same `mise run check` bar — prerequisite for [Phase 19](phase-19.md)
(automated releases).

## Deliverables

### Continuous integration

- **GitHub Actions CI** — `.github/workflows/ci.yml` mirrors `mise run check` (ruff, mypy, pytest,
  frontend typecheck + vitest, OpenAPI types drift check)
- Runs on pull requests and pushes to `main`

### Quality & DX

- structlog redaction on all output (console/JSON + persist/stream); expanded key coverage + tests
- API error surfaces: frontend normalizes FastAPI 422 `detail` arrays for notifications
- OpenAPI → TypeScript types generation (`mise run generate-api-types` / `check-api-types`)
- API smoke test: health → setup/login → list jobs (in-process `TestClient`)

## Key files

- `.github/workflows/ci.yml`
- `scripts/generate-api-types.sh`
- `frontend/src/api/generated/schema.d.ts`
- `backend/tests/api/test_smoke.py`
- `backend/plextraktbox/logstream/handler.py` (`redact_log_processor`)

## Prerequisites

[Phase 8](phase-8.md) recommended — real movie sync gives meaningful e2e coverage; not strictly
required for CI wiring alone.

## Defers to later phases

| Item | Phase |
| ---- | ----- |
| Settings, safety guards, operational health | 13 |
| Dashboard ops view, friendly cron picker | 14 |
| Automated releases / GHCR publish | 19 |
| Doppler maintainer workflow | 15 |
| TrueNAS deploy docs | 22 |

## Verification

[phase-12-test-plan.md](test-plans/phase-12-test-plan.md)

**Next:** [Phase 13 — Settings, safety & operations](phase-13.md)
