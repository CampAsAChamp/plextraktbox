# Phase N verification checklist

> Copy this file to `docs/phase-N-test-plan.md` when phase N is implemented. Replace placeholders,
> delete this block, and link it from [testing.md](testing.md) and [PLAN.md](../PLAN.md#phase-tracker).

**Scope:** _(one-line summary from PLAN.md)_

**Prerequisites:** Phases 0–(N−1) passing. Shared setup: [testing.md](testing.md).

## 1. Automated tests

```bash
mise run test        # add phase-specific test paths here
mise run check       # CI parity before marking phase done
```

- [ ] _(list new test files or behaviors)_

## 2. Container / browser

```bash
mise run up          # or rebuild if phase needs fresh state
```

- [ ] _(manual UI or curl checks)_

## 3. API smoke (optional)

```bash
# curl examples for new endpoints
```

## 4. Reset / fixtures

```bash
# how to wipe state or seed data for re-testing this phase
```

## 5. Notes

_(edge cases, fakes/mocks, external service requirements, etc.)_
