# Phase 3 — Sync engine core

**Status:** Done

## Goal

Port PlexTraktSync-style matching and reconciliation into a service-agnostic engine with
source-of-truth rules, dry-run everywhere, and per-item fault isolation — tested entirely against
in-memory fakes (no live APIs yet).

## Deliverables

- **MediaItem** — service-agnostic model: identifiers (TMDB/IMDb/TVDB + native), watchlist, rating,
  watched, `media_type` (movies first, TV-ready fields)
- **guid.py** — Plex guid parsing; Letterboxd URL → TMDB id → `tmdb://`
- **matcher.py** — index by TMDB → IMDb → TVDB priority; stateless (no persisted mapping)
- **Sources** (`sources/base.py` ABC) — `fetch_*`, `apply_*` (+ `dry_run`), `capabilities`;
  `LetterboxdSource` read-only (`apply_*` raises `NotSupported`)
- **Three reconcilers** — watchlist (Plex truth), ratings (Letterboxd truth), watched (Trakt truth)
- **engine.run** — fetch → plan → log → apply; dry-run skips apply; per-item try/except;
  `RunSummary` counts
- **pluggy** hooks (`plugins.py`) for future extensibility
- Temporary synchronous `POST /api/jobs/{id}/run` for manual testing (replaced by scheduler in
  Phase 4)

## Key files

- `backend/plextraktbox/sync/` — `engine.py`, `media_item.py`, `guid.py`, `matcher.py`,
  `sources/`, `reconcilers/`, `plugins.py`
- `backend/tests/fakes/` — `FakePlex`, `FakeTrakt`, `FakeLetterboxd`, `FakeTMDB`
- `backend/tests/unit/test_reconciler_*.py`, `test_engine.py`

## Prerequisites

[Phase 2](phase-2.md) (connections exist but engine uses fakes, not live clients)

## Defers to later phases

- APScheduler integration (Phase 4)
- Real client-backed fetch/apply (Phase 7)
- TV episode-level logic (Phase 10)

## Verification

[phase-3-test-plan.md](test-plans/phase-3-test-plan.md) — full unit coverage of matching + each reconciler;
dry-run = zero writes.

**Next:** [Phase 4 — Jobs + scheduler](phase-4.md)
