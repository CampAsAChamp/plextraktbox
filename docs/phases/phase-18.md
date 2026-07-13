# Phase 18 — Version & build info

**Status:** Done

## Goal

Show the **running** backend version in the UI (not a hardcoded frontend string) and expose optional
build metadata (git SHA, build time) so it is obvious which build is deployed on TrueNAS or in Docker.

## Deliverables

- **Single source of truth** — `pyproject.toml` `[project].version`; runtime reads via
  `importlib.metadata` (editable install / pip install) with pyproject fallback for bare trees
- **`GET /api/health`** — `version`, optional `git_sha`, optional `built_at` (Pydantic schema)
- **Docker build args** — `GIT_SHA`, `BUILD_TIME` → `PLEXTRAKTBOX_*` env vars in the runtime image
- **Navbar badge** — `ApiHealthBadge` polls `/health` periodically so redeploys update without a
  full page refresh
- **Account menu** — version line (and short SHA when present) for at-a-glance deploy info

## Key files

- `backend/plextraktbox/version_info.py`, `schemas/health.py`, `api/health.py`
- `Dockerfile` — build-arg wiring
- `frontend/src/api/health.ts`, `components/layout/ApiHealthBadge.tsx`, `AppLayout.tsx`

## Prerequisites

None — independent of Phase 7; can ship anytime after Phase 0.

## Defers to later phases

| Item | Phase |
| ---- | ----- |
| Richer health (scheduler alive, DB writable, connection summary) | 13 |
| Versioned GHCR tags in deploy docs | 16–17 |
| Automated semver bumps + GitHub Releases + GHCR publish | 19 |

## Verification

[phase-18-test-plan.md](test-plans/phase-18-test-plan.md)

**Next:** [Phase index](README.md)
