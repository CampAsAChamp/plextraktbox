# Documentation

| Doc | Purpose |
| --- | ------- |
| [architecture.md](architecture.md) | Stack, sync engine, data model, security — the "why" |
| [sync-flows.md](sync-flows.md) | Sync job flow charts + sequence diagrams (per data type) |
| [app-flows.md](app-flows.md) | Container, auth, log streaming, notifications, data model ER |
| [phases/README.md](phases/README.md) | Remaining work (TrueNAS catalog) |
| [testing.md](testing.md) | Smoke tests, automated checks, testing conventions |
| [dev-workflow.md](dev-workflow.md) | Hot reload, Doppler (optional), `api-login`, dev bootstrap |
| [deploy/truenas.md](deploy/truenas.md) | TrueNAS install constraints and milestones |

## Quick links

- **Current focus:** TrueNAS App Catalog ([phases/phase-23.md](phases/phase-23.md))
- **Run checks:** `mise run check`
- **Container smoke test:** `mise run up` → http://localhost:8000
- **Human setup guide:** [README.md](../README.md)

## Layout

```
docs/
├── README.md           ← you are here
├── architecture.md     ← design doc (stable architecture)
├── sync-flows.md       ← sync job Mermaid diagrams
├── app-flows.md        ← container / auth / logs / notifications / ER
├── testing.md          ← verification how-to
├── dev-workflow.md     ← day-to-day dev ergonomics
├── deploy/
│   └── truenas.md      ← TrueNAS deployment
└── phases/
    ├── README.md       ← remaining work
    ├── phase-22.md     ← TrueNAS personal install (done)
    ├── phase-23.md     ← TrueNAS catalog scope (planned)
    ├── phase-25.md     ← ops / OSS hygiene (done)
    └── test-plans/
        ├── phase-22-test-plan.md  ← custom-app / personal install
        ├── phase-23-test-plan.md  ← TrueNAS catalog pre-upload
        └── phase-25-test-plan.md
```
