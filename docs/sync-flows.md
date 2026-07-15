# Sync job flows

Visual companion to [architecture.md](architecture.md). How a job run moves through the
scheduler → engine → sources/reconcilers, and what each data type reads and writes.

Jobs are **per source pair** (`plex_trakt`, `letterboxd_plex`, `letterboxd_trakt`) and enable a
subset of data types. Reconcilers hard-code source-of-truth; Letterboxd is always read-only.

## Source of truth at a glance

```mermaid
flowchart LR
  subgraph watchlist["Watchlist"]
    PWw[Plex truth] -->|add/remove| TWw[Trakt]
  end

  subgraph ratings["Ratings"]
    LBr[Letterboxd truth] -->|rate| PXr[Plex]
    LBr -->|rate| TRr[Trakt]
  end

  subgraph watched["Watched"]
    TRw[Trakt truth] -->|mark watched| PXw[Plex]
  end
```

| Data type | Truth | Writes | Notes |
| --------- | ----- | ------ | ----- |
| Watchlist | Plex | Trakt add/remove | Letterboxd watchlist is ignored (not fetched) |
| Ratings | Letterboxd (0.5–5 → 0–10 at fetch) | Plex (library or Discover), Trakt | Trakt: only update items already in Trakt ratings |
| Watched | Trakt | Plex library mark watched | Unmatched library titles are skipped; LB diary is not a write target |

## Job pairs → services

```mermaid
flowchart TB
  Job[Job: source_pair + data_types] --> Pair{source_pair}

  Pair -->|plex_trakt| PT[Sources: plex, trakt]
  Pair -->|letterboxd_plex| LP[Sources: letterboxd, plex]
  Pair -->|letterboxd_trakt| LT[Sources: letterboxd, trakt]

  PT --> DT{enabled data_types}
  LP --> DT
  LT --> DT

  DT -->|watchlist| W[WatchlistReconciler — plex_trakt only]
  DT -->|ratings| R[RatingsReconciler — needs letterboxd]
  DT -->|watched| H[WatchedReconciler]
```

Validation (from `Job.validate_data_types`): watchlist requires `plex_trakt`; ratings requires
Letterboxd in the pair.

## Run lifecycle

End-to-end path for every scheduled or “run now” execution.

```mermaid
sequenceDiagram
  autonumber
  participant Trig as Cron / Run now
  participant Sched as scheduler.manager
  participant Run as scheduler.runner
  participant SF as source_factory
  participant Eng as sync.engine
  participant Rec as Reconciler
  participant Src as Source adapters
  participant Log as logstream + DB
  participant N as notifications

  Trig->>Sched: trigger job
  Sched->>Run: execute_run(job_id)
  Run->>Run: create JobRun(running), bind per-run logger
  Run->>SF: build_sources(connections)
  SF-->>Run: plex / trakt / letterboxd Sources
  Run->>Eng: run_sync(ctx)

  loop each enabled data_type
    Eng->>Rec: plan(ctx)
    Rec->>Src: fetch truth + targets (cached in ctx)
    Src-->>Rec: MediaItem lists
    Rec-->>Eng: ReconcilePlan (PlannedChanges)
    Eng->>Log: log "would X" / "will X"
    alt dry_run
      Eng->>Eng: skip apply
    else live
      Eng->>Src: apply_* (grouped by target + action)
      Note over Eng,Src: per-batch try/except — one failure ≠ abort
    end
  end

  Eng-->>Run: RunSummary
  Run->>Log: finalize JobRun status + summary
  Run->>N: dispatch Discord / in-app
```

Inside the engine, the shape is always **fetch → plan → log → apply**:

```mermaid
flowchart LR
  A[before_run hooks] --> B[For each data_type]
  B --> C[reconciler.plan]
  C --> D[Log each PlannedChange]
  D --> E{dry_run?}
  E -->|yes| F[Skip apply]
  E -->|no| G[Group by target + action]
  G --> H[source.apply_*]
  H --> I[Merge ApplyResult into RunSummary]
  F --> J[after_run hooks]
  I --> J
  J --> K[RunSummary]
```

## Matching

Items are matched **statelessly** by identifier priority (no persisted Plex↔Trakt mapping table):

```mermaid
flowchart LR
  Item[MediaItem identifiers] --> M{MediaMatcher}
  M -->|1st| TMDB[tmdb]
  M -->|2nd| IMDb[imdb]
  M -->|3rd| TVDB[tvdb]
```

Letterboxd titles resolve `letterboxd.com/...` → TMDB id (via TMDB client) → `tmdb://` before match.

**Planned ([Phase 21](phases/phase-21.md)):** Letterboxd CSV export TTL + slug→ids; Trakt list TTL;
Plex Discover key map; Plex library loaded once per run. Cross-service matching remains ID-based.

---

## Watchlist — Plex → Trakt

**Job:** `plex_trakt` with `watchlist` enabled.  
**Truth:** Plex. **Write target:** Trakt. Letterboxd watchlist is not loaded for `plex_trakt` jobs.

```mermaid
sequenceDiagram
  autonumber
  participant Eng as Engine
  participant Rec as WatchlistReconciler
  participant Plex as PlexSource
  participant Trakt as TraktSource

  Eng->>Rec: plan(ctx)
  Rec->>Plex: fetch_watchlist
  Plex-->>Rec: Plex watchlisted items (truth)
  Rec->>Trakt: fetch_watchlist
  Trakt-->>Rec: Trakt watchlisted items

  Note over Rec: Match by TMDB→IMDb→TVDB<br/>In Plex not Trakt → ADD<br/>In Trakt not Plex → REMOVE

  Rec-->>Eng: plan (ADD/REMOVE on trakt)
  Eng->>Trakt: apply_watchlist(changes, dry_run)
  Trakt-->>Eng: ApplyResult
```

```mermaid
flowchart TB
  Truth[Plex watchlist] --> Diff{Diff vs Trakt}
  Diff -->|missing on Trakt| Add[ADD → Trakt]
  Diff -->|extra on Trakt| Rem[REMOVE → Trakt]
  Diff -->|matched| Skip[no change]
```

---

## Ratings — Letterboxd → Plex + Trakt

**Jobs:** `letterboxd_plex` and/or `letterboxd_trakt` with `ratings` enabled.  
**Truth:** Letterboxd. **Write targets:** Plex and/or Trakt (whichever sources are in the job).

Ratings are normalized to **0–10** when building Letterboxd `MediaItem`s (stars × 2).

```mermaid
sequenceDiagram
  autonumber
  participant Eng as Engine
  participant Rec as RatingsReconciler
  participant LB as LetterboxdSource
  participant Plex as PlexSource
  participant Trakt as TraktSource

  Eng->>Rec: plan(ctx)
  Rec->>LB: fetch_ratings
  LB-->>Rec: rated items (0–10 scale)

  alt plex in job
    Rec->>Plex: fetch_ratings (scoped libraries)
    Plex-->>Rec: library-rated items
    Note over Rec: Match LB → Plex<br/>No library match + has IDs → still plan UPDATE<br/>(apply uses Discover fallback)<br/>Within tolerance → skip
  end

  alt trakt in job
    Rec->>Trakt: fetch_ratings
    Trakt-->>Rec: existing Trakt ratings
    Note over Rec: Only UPDATE when already present on Trakt<br/>(no create-from-scratch for Trakt ratings)
  end

  Rec-->>Eng: plan (UPDATE on plex / trakt)
  Eng->>Plex: apply_ratings (library rate or Discover)
  Eng->>Trakt: apply_ratings
```

### Plex apply: library vs Discover

```mermaid
flowchart TB
  Change[PlannedChange: rate on plex] --> HasLib{Matched library item<br/>in scoped libraries?}
  HasLib -->|yes| Lib[video.rate via plexapi<br/>com.plexapp.plugins.library]
  HasLib -->|no, has TMDB/IMDb| Disc[Discover rate API<br/>discover.provider.plex.tv]
  HasLib -->|no IDs| Skip[skip / unmatched]
```

Friend-shared libraries are **not** your library — ratings land on Discover metadata, not the
shared server’s library page. See [architecture.md](architecture.md#plex-ratings-discover-vs-library).

---

## Watched — Trakt → Plex

**Job:** typically `plex_trakt` with `watched` enabled.  
**Truth:** Trakt. **Write target:** Plex (library mark watched). Only items that already exist in
the scoped Plex library are planned.

```mermaid
sequenceDiagram
  autonumber
  participant Eng as Engine
  participant Rec as WatchedReconciler
  participant Trakt as TraktSource
  participant Plex as PlexSource

  Eng->>Rec: plan(ctx)
  Rec->>Trakt: fetch_watched
  Trakt-->>Rec: Trakt watched movies (truth)
  Rec->>Plex: fetch_watched / library items
  Plex-->>Rec: Plex library items

  Note over Rec: Match by IDs<br/>Trakt watched + Plex match + not watched → UPDATE<br/>No Plex library match → skip

  Rec-->>Eng: plan (UPDATE watched on plex)
  Eng->>Plex: apply_watched → mark library movies watched
  Note over Trakt: Trakt is never a watched write target
```

```mermaid
flowchart LR
  T[Trakt watched] -->|match in library| P[Plex]
  T -->|no library match| S[skip]
  P -->|already watched| Skip[no change]
  P -->|unwatched| MW[mark watched]
```

---

## Dry-run

Dry-run is resolved per run: `override ?? job.dry_run ?? global`. The same plan and log path run;
apply is skipped and messages use **“would …”** instead of **“will …”**. Zero third-party writes.

## Where the code lives

| Step | Code |
| ---- | ---- |
| Trigger + JobRun | `scheduler/runner.py` |
| Build sources | `services/source_factory.py` |
| Orchestration | `sync/engine.py` |
| Plans | `sync/reconcilers/{watchlist,ratings,watched}.py` |
| Fetch / apply | `sync/sources/{plex,trakt,letterboxd}_source.py` + `clients/` |
| Match | `sync/matcher.py`, `sync/guid.py` |
