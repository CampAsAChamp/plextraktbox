# Phase 1 verification checklist

Auth + first-run setup wizard: single local user, bcrypt password, session cookie, setup gate,
login/logout, SPA routing (`/setup` → `/login` → dashboard).

**Prerequisites:** [Phase 0](phase-0-test-plan.md) passing. Shared container setup: [testing.md](testing.md).

## 1. Automated tests

```bash
mise run test-backend    # backend/tests/api/test_auth.py
mise run test-frontend   # frontend/src/App.test.tsx (routing gates)
# or: mise run test
```

Covers: setup status, user creation, CSRF header on mutating requests, login with username or
email, `/api/auth/me` session check, logout, setup disabled after first user (409).

## 2. Container — first-run wizard

Start with a **fresh** database (no user yet):

```bash
mise run rebuild   # or: mise run down-v && mise run up
```

Open http://localhost:8000 and verify:

1. App redirects to `/setup` — "Welcome to plextraktbox"
2. Create admin account (username, email, password) → lands on dashboard
3. Dashboard shows signed-in user and green health badge
4. Sign out → `/login`
5. Sign in again (username or email) → dashboard
6. Visit `/setup` after setup → cannot create a second user

## 3. API smoke (optional)

With the container running on a fresh DB:

```bash
curl -s http://localhost:8000/api/setup/status
# → {"needs_setup":true}

curl -s -X POST http://localhost:8000/api/setup/user \
  -H 'Content-Type: application/json' \
  -H 'X-Requested-With: XMLHttpRequest' \
  -d '{"username":"nick","email":"nick@example.com","password":"supersecret"}'
# → 201 with user JSON

curl -s http://localhost:8000/api/setup/status
# → {"needs_setup":false}
```

Second `POST /api/setup/user` should return **409**.

## 4. Reset for re-testing

```bash
mise run down-v
mise run up
```

Local dev (no container): `mise run clean-data && mise run db-upgrade`, then restart
`dev-backend`.
