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
| `backend/pyproject.toml` `[project].version` | **Runtime source of truth** — read via `version_info.py` / `/api/health` |
| Root `package.json` `version` | semantic-release home for the single app semver (private meta package) |
| `frontend/package.json` `version` | Kept in lockstep by the release prepare step (SPA metadata; UI still reads API) |

The badge label says “API” because it confirms the backend is reachable, but the **version string is
the whole app** (backend + bundled frontend from the same image). In dev with split Vite + uvicorn,
the UI still shows the **backend** version — that is intentional: production is one container, and the
API is the runtime source of truth.

Optional `git_sha` / `built_at` on `/health` (Phase 18) complement semver when diagnosing “which
build is running?” on TrueNAS.

## What shipped

### Version bump automation

- **semantic-release** on push to `main` — no Release PR
- Bumps root `package.json`, syncs `backend/pyproject.toml` + `frontend/package.json`, updates
  `CHANGELOG.md`, commits `chore(release): X.Y.Z [skip ci]`, tags `vX.Y.Z`, creates GitHub Release
- **Conventional Commits** required for anything that lands on `main` (direct push or squash-merge
  PR title: `feat:` / `fix:` / `feat!:`). Enforced by `.githooks/commit-msg` (`mise run install`)
  and `.github/workflows/pr-title.yml`

### GitHub Release + GHCR

- Same workflow run publishes `ghcr.io/campasachamp/plextraktbox:vX.Y.Z` (+ `:latest`) after a new
  release (`GITHUB_TOKEN` tags do not re-trigger workflows)
- Manual `v*` tags also publish via the same workflow’s `publish-tag` job
- Build args: `GIT_SHA`, `BUILD_TIME` (Phase 18)
- Release job runs `mise run check` before bumping / publishing

### Maintainer setup (GitHub UI)

- Prefer **squash-merge** on `main`
- After the first package push: set the GHCR package visibility to **public** (needed for TrueNAS)
- Workflow `permissions:` cover contents / issues / PRs / packages; no separate PAT required

## Key files

- `.github/workflows/ci.yml` — Phase 12 check gate
- `.github/workflows/pr-title.yml` — Conventional Commit PR titles
- `.github/workflows/release.yml` — semantic-release + GHCR publish
- `.githooks/commit-msg` — local Conventional Commit enforcement
- `.releaserc.json` — semantic-release plugins (inline prepare syncs backend / frontend)
- Root `package.json` — semantic-release version home
- `CHANGELOG.md` — maintained by semantic-release

## Defers to later phases

| Item | Phase |
| ---- | ----- |
| TrueNAS install steps using GHCR tags | 22 |
| Catalog app pointing at published image | 23 |

## Verification

[phase-19-test-plan.md](test-plans/phase-19-test-plan.md)

**Next:** [Phase 20 — Mobile & responsive layout](phase-20.md) (product UI track; independent of release/deploy)
