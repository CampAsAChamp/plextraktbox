# Phase 18 verification checklist

**Scope:** Running version + build metadata in `/api/health` and the UI — see [phase-18.md](../phase-18.md).

**Prerequisites:** Phases 0–6 passing. Shared setup: [testing.md](../../testing.md).

## 1. Automated tests

```bash
mise run test-backend   # version_info + health API
mise run test-frontend  # if health hook tests added
mise run check
```

- [ ] `tests/unit/test_version_info.py` — version resolves from installed package / pyproject fallback
- [ ] `tests/api/test_health.py` — response includes `version`; optional `git_sha` / `built_at` when env set

## 2. Container / browser

```bash
mise run up
```

- [ ] `curl -s http://localhost:8000/api/health` → JSON with `version` matching `backend/pyproject.toml`
- [ ] Navbar badge shows `✓ API · v…` from the response (not a frontend constant)
- [ ] Account menu shows matching version line
- [ ] After rebuilding the image with a bumped `pyproject.toml` version, badge updates within ~60s
  without hard refresh (or immediately on refresh)

## 3. Docker build metadata (optional)

```bash
docker build --build-arg GIT_SHA=$(git rev-parse HEAD) --build-arg BUILD_TIME=$(date -u +%Y-%m-%dT%H:%M:%SZ) -t plextraktbox:test .
docker run --rm -p 8000:8000 plextraktbox:test
curl -s http://localhost:8000/api/health
```

- [ ] Response includes `git_sha` and `built_at`; UI shows short SHA in badge / account menu

## 4. Notes

- Dev (`mise run dev-backend` + Vite): badge reflects **backend** version; frontend `package.json`
  version is not shown (single-container deploy uses API as truth).
- Phase 13 adds operational health fields; this phase only covers version/build identity.
