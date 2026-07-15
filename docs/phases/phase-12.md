# Phase 12 — CI & quality

**Status:** Planned

## Goal

Restore automated checks in GitHub Actions and tighten quality gates so releases and day-to-day
development share the same `mise run check` bar — prerequisite for [Phase 19](phase-19.md)
(automated releases).

## Deliverables

### Continuous integration

- **GitHub Actions CI** — `.github/workflows/ci.yml` mirrors `mise run check` (ruff, mypy, pytest,
  frontend typecheck + vitest)
- Runs on pull requests and pushes to `main`

### Quality & DX

- structlog redaction audit; improve error surfaces in API/UI
- OpenAPI → TypeScript types generation
- e2e smoke test (minimal happy path: health → login → list jobs)

## Key files (expected)

- `.github/workflows/ci.yml`
- Optional: `scripts/generate-api-types.sh`, e2e test harness

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

Test plan TBD when phase lands — copy [phase-test-plan-template.md](test-plans/phase-test-plan-template.md).

**Next:** [Phase 13 — Settings, safety & operations](phase-13.md)
