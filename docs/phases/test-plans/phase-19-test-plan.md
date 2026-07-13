# Phase 19 verification checklist

**Scope:** Automated semver bumps, GitHub Releases, GHCR publish — see [phase-19.md](../phase-19.md).

**Prerequisites:** Phase 18 done; Phase 12 CI in place. Shared setup: [testing.md](../../testing.md).

## 1. Release PR flow

- [ ] Merge to `main` with release-worthy changes triggers (or manually run) release-please
- [ ] Release PR updates `backend/pyproject.toml` version and `CHANGELOG.md`
- [ ] Merging release PR creates git tag `vX.Y.Z` and GitHub Release

## 2. CI gate

- [ ] Release / publish workflow does **not** run if `mise run check` failed on the tagged commit
- [ ] CI workflow mirrors local `mise run check` (ruff, mypy, pytest, vitest)

## 3. Container publish

```bash
# After a release, on a machine with ghcr pull access:
docker pull ghcr.io/<owner>/plextraktbox:vX.Y.Z
docker run --rm -p 8000:8000 ghcr.io/<owner>/plextraktbox:vX.Y.Z
curl -s http://localhost:8000/api/health
```

- [ ] Image tag matches release semver
- [ ] `/api/health` `version` matches tag (without `v` prefix)
- [ ] `git_sha` and `built_at` populated from CI build args

## 4. UI end-to-end

- [ ] Deploy released image (or pull locally); navbar badge shows new semver without code changes
- [ ] Account menu version line matches `/api/health`

## 5. Docs

- [ ] [deploy/truenas.md](../../deploy/truenas.md) documents which GHCR tag to pull
- [ ] README notes how maintainers cut a release (merge release PR vs manual tag)

## 6. Notes

- Personal repo uses plain commit subjects — configure release-please manifest mode accordingly
  (not conventional-commit parser unless we adopt that style later).
- `frontend/package.json` version sync is optional; UI never reads it.
