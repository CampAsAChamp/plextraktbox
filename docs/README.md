# Documentation

| Doc | Purpose |
| --- | ------- |
| [architecture.md](architecture.md) | Stack, sync engine, data model, security — the "why" |
| [phases/README.md](phases/README.md) | **Phase index** (status, scope, test plans) |
| [testing.md](testing.md) | Smoke tests, automated checks, testing conventions |
| [dev-workflow.md](dev-workflow.md) | Hot reload, `api-login`, dev bootstrap |
| [deploy/truenas.md](deploy/truenas.md) | TrueNAS install constraints and milestones |

## Quick links

- **Current focus:** Phase 7 — [client-backed fetch (movies)](phases/phase-7.md)
- **Run checks:** `mise run check`
- **Container smoke test:** `mise run up` → http://localhost:8000
- **Human setup guide:** [README.md](../README.md)

## Layout

```
docs/
├── README.md           ← you are here
├── architecture.md     ← design doc (stable architecture)
├── testing.md          ← verification how-to
├── dev-workflow.md     ← day-to-day dev ergonomics
├── deploy/
│   └── truenas.md      ← TrueNAS deployment
└── phases/
    ├── README.md       ← single phase progress table
    ├── phase-N.md      ← scope per phase
    └── test-plans/     ← verification checklists
```

When a phase lands: update its [phases/phase-N.md](phases/phase-0.md) doc and the table in
[phases/README.md](phases/README.md); copy
[phases/test-plans/phase-test-plan-template.md](phases/test-plans/phase-test-plan-template.md) →
`phases/test-plans/phase-N-test-plan.md`.
