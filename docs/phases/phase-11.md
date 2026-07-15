# Phase 11 — TV sync

**Status:** Planned

## Goal

Extend client-backed sources and reconcilers to **shows and episodes** — watchlist, ratings, and
watched/history where each service supports them — building on the movie path proven in Phases 7–8.

## Deliverables

### Source extensions

- Plex/Trakt fetch + apply for TV libraries and episode-level watched state
- Episode-level **Trakt ↔ Plex** watched matching (not just show-level)
- `media_type` handling throughout engine and reconcilers for `show` / `episode`
- Letterboxd remains **film-focused** — read-only; no TV write-back

### Matching

- TVDB identifier priority where relevant (already scaffolded in `guid.py` / `matcher.py`)
- Unmatched-items report includes episode-level gaps

### Jobs & UI

- Job data-type and source-pair options reflect TV scope where applicable
- Run summary counts break out shows/episodes as needed
- Job form changes on the existing Mantine UI

## Key files (expected)

- `backend/plextraktbox/sync/sources/`, `reconcilers/`, `clients/plex_client.py`,
  `trakt_client.py`
- Tests: fakes extended for TV fixtures; respx mapping tests for show/episode payloads

## Prerequisites

[Phases 7–8](phase-7.md) — **movies working on real data**

## Defers to later phases

| Item | Phase |
| ---- | ----- |
| Global settings, dry-run guards, exclude list | 13 |
| Dashboard ops view, schedule picker | 14 |
| Doppler maintainer workflow | 15 |
| TrueNAS packaging, GHCR, reverse proxy | 22 |

## Verification

Test plan TBD when phase lands.

**Next:** [Phase 12 — CI & quality](phase-12.md)
