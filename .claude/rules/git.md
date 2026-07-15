# Git (personal repo)

- Plain imperative subject lines — **no** conventional commits (`feat:`, `fix:`) in local commits unless the user asks
- No trailing period on subject lines (e.g. `Add job scheduler UI`, not `Add job scheduler UI.`)
- Match recent `git log` in this repo (e.g. `Add job scheduler UI`, `Fix Trakt token refresh`)
- Optional short body focusing on **why**
- No Jira IDs
- Only commit when explicitly requested; never push unless asked

**Releases (Phase 19):** When squash-merging a PR to `main` that should trigger a version bump, use a Conventional Commit **PR title** (`feat:`, `fix:`, `feat!:`). semantic-release parses that squash commit; local branch commits stay plain.
