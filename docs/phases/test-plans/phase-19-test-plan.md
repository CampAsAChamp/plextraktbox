# Phase 19 verification checklist

**Scope:** Automated semver bumps, GitHub Releases, GHCR publish — see [phase-19.md](../phase-19.md).

**Prerequisites:** Phase 18 done; Phase 12 CI in place. Shared setup: [testing.md](../../testing.md).

## 1. Release flow

- [ ] Squash-merge to `main` with a Conventional Commit title (`feat: …` / `fix: …`)
- [ ] semantic-release bumps root `package.json`, `backend/pyproject.toml`,
      `frontend/package.json`, and `CHANGELOG.md` to the **same** semver (no Release PR)
- [ ] git tag `vX.Y.Z` and a GitHub Release are created in the same workflow run
- [ ] Same run publishes the GHCR image (does not rely on the tag triggering another workflow)

## 2. CI gate

- [ ] Release job runs `mise run check` and does **not** bump/publish if that step fails
- [ ] CI workflow mirrors local `mise run check` (ruff, mypy, pytest, vitest)

## 3. Container publish

```bash
# After a release (package must be public, or you must be authenticated to GHCR):
docker pull ghcr.io/campasachamp/plextraktbox:vX.Y.Z
docker run --rm -p 8000:8000 ghcr.io/campasachamp/plextraktbox:vX.Y.Z
curl -s http://localhost:8000/api/health
```

- [ ] Image tag matches release semver
- [ ] `/api/health` `version` matches tag (without `v` prefix)
- [ ] `git_sha` and `built_at` populated from CI build args

## 4. UI end-to-end

- [ ] Deploy released image (or pull locally); navbar badge shows new semver without code changes
- [ ] Account menu version line matches `/api/health`

## 5. Docs

- [ ] [deploy/truenas.md](../../deploy/truenas.md) documents GHCR image name and tags
- [ ] README has a Releases section (squash titles, automatic release, pull image)

## 6. Notes

- Local commits stay plain imperative subjects. Only the **squash-merge PR title on `main`** needs
  Conventional Commits so semantic-release can bump.
- After the first image push: GitHub → Packages → `plextraktbox` → Package settings → change
  visibility to **public** (required for unauthenticated TrueNAS pulls in Phase 22).
- Manual tags: `git tag vX.Y.Z && git push origin vX.Y.Z` runs the `publish-tag` job in
  `.github/workflows/release.yml`.
