# App flows

Visual companion to [architecture.md](architecture.md) for non-sync paths: container shape,
auth/setup, live logs, notifications, and the SQLite data model.

Sync job diagrams live in [sync-flows.md](sync-flows.md).

## Container / process shape

One Docker image, one process tree: FastAPI serves the built SPA and API, APScheduler runs
in-process, SQLite + caches live on the `/data` volume (ZFS mount on TrueNAS).

```mermaid
flowchart TB
  subgraph host["Host / TrueNAS"]
    Vol["/data volume<br/>SQLite, caches, themes, backups"]
  end

  subgraph container["plextraktbox container"]
    Uvicorn[uvicorn → FastAPI]
    SPA[Static React SPA]
    API["/api/*"]
    Sched[APScheduler<br/>AsyncIOScheduler]
    Eng[sync.engine / runner]

    Uvicorn --> SPA
    Uvicorn --> API
    Uvicorn --> Sched
    Sched --> Eng
    API --> Eng
  end

  Vol <-->|"DATA_DIR=/data"| container
  Browser[Browser] -->|HTTP :PORT default 8000| Uvicorn
```

Listen port defaults to **8000** (`PORT` env). Secrets stay in env / Fernet-encrypted DB columns —
never baked into the image.

---

## First-run / auth gate

Single local user. Until that user exists, the SPA is locked to the setup wizard; afterward,
session cookie auth gates the app. Mutating API calls also require `X-Requested-With: XMLHttpRequest`
(CSRF).

```mermaid
flowchart TB
  Start[App load] --> Status["GET /api/setup/status"]
  Status -->|needs_setup| Wizard[Setup wizard<br/>POST /api/setup/user]
  Wizard --> Login

  Status -->|user exists| Me["GET /api/auth/me"]
  Me -->|401| Login[Login page<br/>POST /api/auth/login]
  Me -->|200| App[App routes]
  Login -->|session cookie| App

  App --> Mutate{Mutating request?}
  Mutate -->|yes| CSRF{X-Requested-With<br/>= XMLHttpRequest?}
  CSRF -->|no| Reject[400]
  CSRF -->|yes| Authed[CurrentUserDep]
  Mutate -->|GET / SSE| Authed
```

Public exceptions: `/api/setup/*` (self-disables once a user exists) and `/api/health`.

---

## Live log streaming

Per-run structlog → persist + publish → SSE to the React LogViewer. Reconnect uses `?after_id=`
so clients resume without duplicates.

```mermaid
sequenceDiagram
  autonumber
  participant Run as scheduler.runner
  participant Log as structlog + logstream.handler
  participant DB as log_entry table
  participant Hub as logstream.pubsub
  participant SSE as GET /api/runs/{id}/logs/stream
  participant UI as LogViewer

  Run->>Log: bind per-run logger
  Log->>DB: async write queue → LogEntry
  Log->>Hub: publish to RunChannel<br/>(ring buffer ~500)

  UI->>SSE: connect (?after_id)
  SSE->>DB: replay rows since after_id
  SSE->>Hub: ring backlog since after_id
  SSE-->>UI: historical + backlog events

  alt run still running
    Hub-->>SSE: live subscriber queue
    SSE-->>UI: live log events
    Run->>Hub: close(status)
    Hub-->>SSE: end event
    SSE-->>UI: end → stop stream
  else run already finished
    SSE-->>UI: end with terminal status
  end
```

UI reconnects with `fetch-event-source` and the last seen `after_id`. Completed runs can also
page historical rows via REST through the same LogViewer component.

---

## Notification fan-out

Called at run finalize (never aborts the run). Job `notify_mode` chooses inherit (global configs)
vs job-scoped configs vs disabled; each matching channel is sent concurrently and isolated.

```mermaid
sequenceDiagram
  autonumber
  participant Run as scheduler.runner
  participant Disp as notifications.dispatcher
  participant Cfg as notification_config
  participant D as Discord
  participant I as in-app bell

  Run->>Disp: dispatch_notifications(job, run)
  Disp->>Disp: build_payload(RunSummary)
  Disp->>Cfg: resolve_configs<br/>(inherit → global / else job scope)
  Cfg-->>Disp: enabled configs matching status

  par isolated channels
    Disp->>D: send_discord (httpx embed)
  and
    Disp->>I: send_inapp (insert row)
  end

  Note over Disp: per-channel try/except — failure logs WARN only
```

`POST /api/notifications/{id}/test` sends a synthetic payload through the same path.

---

## Data model (SQLite)

Core tables and relationships. Sync caches (`letterboxd_slug_cache`, `trakt_list_cache`,
`plex_discover_key_cache`) and APScheduler’s `apscheduler_jobs` share the same DB file under
`/data`.

```mermaid
erDiagram
  user {
    int id PK
    string username
    string email
    string password_hash
  }

  connection {
    int id PK
    string service UK
    string status
    string config_json
    bytes secret_enc
  }

  job ||--o{ job_run : has
  job {
    int id PK
    string name
    string source_pair
    bool enabled
    string cron
    bool dry_run
    string data_types_json
  }

  job_run ||--o{ log_entry : emits
  job_run {
    int id PK
    int job_id FK
    string status
    bool dry_run
    string summary_json
  }

  log_entry {
    int id PK
    int run_id FK
    datetime ts
    string level
    string message
  }

  job ||--o{ notification_config : may_override
  notification_config {
    int id PK
    string channel
    string scope
    int job_id FK
    bool enabled
  }

  job_run ||--o{ inapp_notification : may_link
  inapp_notification {
    int id PK
    int run_id FK
    string level
    string title
    bool read
  }

  setting {
    string key PK
    string value_json
  }
```

`user` is a single-row table (enforced in app); `connection` is one row per service (unique
`service`) with no FK to user. `connection.secret_enc` is Fernet-encrypted (key derived from
`SECRET_KEY`). Job ↔ run and run ↔ log links are by indexed `job_id` / `run_id` (not ORM
relationships).
