# Phase 15 verification checklist

**Scope:** Optional Doppler secrets for maintainers — see [phase-15.md](../phase-15.md).

**Prerequisites:** Phase 12 CI passing. Shared setup: [testing.md](../../testing.md). Doppler CLI +
project access required only for the maintainer path below; default `.env` path still works.

## 1. Automated tests

```bash
mise run check          # default CI path (stub/local .env) — no Doppler required
# or, for maintainers with Doppler CLI set up:
mise run check-doppler  # doppler run -- mise run check
```

- [ ] `mise run check` still passes without Doppler (dummy or local `.env`)
- [ ] With Doppler CLI + `local` secrets populated: `mise run check-doppler` passes without editing
      `SECRET_KEY` / Trakt client vars in `.env`

## 2. Container / browser

```bash
doppler login && doppler setup   # once — reads doppler.yaml
mise run up-dev                  # Doppler + hot reload (default)
# or: mise run up-doppler
curl -s http://localhost:8000/api/health
```

- [ ] Fresh clone (or secrets removed from `.env`): `mise run up-doppler` boots and
      `/api/health` is OK
- [ ] `mise run up` / `mise run up-dev-env` still work with a normal `.env` (no Doppler)
- [ ] TrueNAS / self-host path unchanged — env vars from app config, not Doppler

## 3. API smoke (optional)

```bash
mise run api-login   # uses DEV_* from Doppler and/or .env
curl -s -b cookies.txt http://localhost:8000/api/jobs
```

## 4. Reset / fixtures

```bash
# No DB migration for this phase.
# If you rotate SECRET_KEY in Doppler, re-auth connections or run:
mise run dev-reencrypt-secrets
```

## 5. Notes

- Doppler is **maintainer-only**. Self-hosted installs never need the CLI or a service token.
- Default GitHub Actions continues to stub `.env`; do not put real credentials in the workflow file.
- Optional future integration job: `DOPPLER_TOKEN` (service token → config `ci`) + `doppler run --`.
- `docker-compose.dev.yml` passes `SECRET_KEY` / Trakt client vars from the host environment so
  `doppler run` works without an `env_file`.
