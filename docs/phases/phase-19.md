# Phase 19 — Automated versioning & GitHub releases

**Status:** Planned

## Goal

Automate version bumps, GitHub Releases, and container publishing so the number shown in the UI
([Phase 18](phase-18.md)) always matches a tagged, reproducible deploy — no manual edits across
multiple files.

## Context — one app version, not two

plextraktbox ships as a **single Docker image** (FastAPI + baked-in SPA). There is only one
**deployed app version**:

| What | Role today |
| ---- | ---------- |
| `backend/pyproject.toml` `[project].version` | **Source of truth** — read at runtime via `version_info.py` |
| `GET /api/health` → `version` | What the navbar badge and account menu display |
| `frontend/package.json` `version` | npm metadata only; **not** shown in the UI and can drift — Phase 19 syncs or stops tracking it separately |

The badge label says “API” because it confirms the backend is reachable, but the **version string is
the whole app** (backend + bundled frontend from the same image). In dev with split Vite + uvicorn,
the UI still shows the **backend** version — that is intentional: production is one container, and the
API is the runtime source of truth.

Optional `git_sha` / `built_at` on `/health` (Phase 18) complement semver when diagnosing “which
build is running?” on TrueNAS.

## Deliverables

### Version bump automation

- **release-please** (or equivalent) manifest targeting `backend/pyproject.toml`
- Release PR bumps semver, updates `CHANGELOG.md`, and optionally syncs `frontend/package.json`
  (cosmetic — keep in step or drop frontend `version` from release scope)
- Tag format: `vX.Y.Z` matching pyproject version

### GitHub Release

- Merging the release PR (or pushing the tag) creates a **GitHub Release** with generated notes
- Attach or link build artifacts if useful (optional — image is primary deliverable)

### Publish container image

- Workflow on release tag: build `Dockerfile`, pass `GIT_SHA` + `BUILD_TIME` (Phase 18 build args)
- Push to **GHCR** as `ghcr.io/<owner>/plextraktbox:vX.Y.Z` (+ `:latest` on stable releases)
- Document pull/tag usage in [deploy/truenas.md](../deploy/truenas.md) (feeds [Phase 16](phase-16.md))

### CI integration

- Depends on [Phase 12](phase-12.md) CI (`.github/workflows/ci.yml` runs `mise run check`)
- Release workflow must not publish unless CI passed on the tagged commit

## Key files (expected)

- `.github/workflows/ci.yml` — from Phase 12
- `.github/workflows/release.yml` — release-please + GHCR publish
- `release-please-config.json` — manifest + component for Python package
- `backend/pyproject.toml` — bumped version field
- `CHANGELOG.md` — maintained by release tooling

## Prerequisites

- [Phase 18](phase-18.md) — runtime version + build metadata in `/health` and UI (**done**)
- [Phase 12](phase-12.md) — CI workflow; release gates on green check
- GHCR permissions / `GITHUB_TOKEN` or PAT for package write (documented alongside [Phase 16](phase-16.md))

## Defers to later phases

| Item | Phase |
| ---- | ----- |
| TrueNAS install steps referencing GHCR tags | 16 |
| Catalog app pointing at published image | 17 |
| Doppler tokens for CI secrets | 15 (optional) |

## Verification

[phase-19-test-plan.md](test-plans/phase-19-test-plan.md)

**Next:** [Phase 20 — Mobile & responsive layout](phase-20.md) (product UI track; independent of release/deploy)
