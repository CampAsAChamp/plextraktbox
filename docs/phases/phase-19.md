# Phase 19 — Automated versioning & GitHub releases

**Status:** Done

## Goal

Automate version bumps, GitHub Releases, and container publishing so the number shown in the UI
([Phase 18](phase-18.md)) always matches a tagged, reproducible deploy — no manual edits across
multiple files.

## Context — one app version, not two

plextraktbox ships as a **single Docker image** (FastAPI + baked-in SPA). There is only one
**deployed app version**:

| What | Role |
| ---- | ---- |
| `backend/pyproject.toml` `[project].version` | **Source of truth** — read at runtime via `version_info.py` |
| `GET /api/health` → `version` | What the navbar badge and account menu display |
| `frontend/package.json` `version` | Cosmetic npm metadata only; not bumped by release-please |

The badge label says “API” because it confirms the backend is reachable, but the **version string is
the whole app** (backend + bundled frontend from the same image). In dev with split Vite + uvicorn,
the UI still shows the **backend** version — that is intentional: production is one container, and the
API is the runtime source of truth.

Optional `git_sha` / `built_at` on `/health` (Phase 18) complement semver when diagnosing “which
build is running?” on TrueNAS.

## What shipped

### Version bump automation

- **release-please** manifest: package path `backend`, `release-type: python`
- Release PR bumps `backend/pyproject.toml` and `backend/CHANGELOG.md`
  (`frontend/package.json` is not synced — release-please forbids `..` paths outside the package)
- Tag format: `vX.Y.Z` (`include-component-in-tag: false`)
- **Squash-merge with Conventional Commit PR titles** (`feat:` / `fix:` / `feat!:`) when landing on
  `main` — local day-to-day subjects stay plain; release-please parses the squash commit

### GitHub Release + GHCR

- Merging the Release Please PR creates a GitHub Release and tag
- Publish runs in `.github/workflows/release-please.yml` when `release_created` (same workflow run —
  tags created with `GITHUB_TOKEN` do not trigger other workflows)
- `.github/workflows/release.yml` covers **manual** `v*` tags (`git push origin vX.Y.Z`)
- Image: `ghcr.io/campasachamp/plextraktbox:vX.Y.Z` and `:latest`
- Build args: `GIT_SHA`, `BUILD_TIME` (Phase 18)
- Publish job runs `mise run check` before `docker build` / push

### Maintainer setup (GitHub UI)

- Prefer **squash-merge** on `main`
- After the first package push: set the GHCR package visibility to **public** (needed for TrueNAS)
- Workflow `permissions:` cover contents / PRs / packages; no separate PAT required for GHCR

## Key files

- `.github/workflows/ci.yml` — Phase 12 check gate
- `.github/workflows/release-please.yml` — release-please + publish on release
- `.github/workflows/release.yml` — publish on manual `v*` tags
- `release-please-config.json` / `.release-please-manifest.json`
- `backend/pyproject.toml` — bumped version field
- `backend/CHANGELOG.md` — maintained by release-please

## Defers to later phases

| Item | Phase |
| ---- | ----- |
| TrueNAS install steps using GHCR tags | 22 |
| Catalog app pointing at published image | 23 |

## Verification

[phase-19-test-plan.md](test-plans/phase-19-test-plan.md)

**Next:** [Phase 20 — Mobile & responsive layout](phase-20.md) (product UI track; independent of release/deploy)
