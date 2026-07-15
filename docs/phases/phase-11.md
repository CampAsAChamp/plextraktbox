# Phase 11 — TV sync

**Status:** Done

## Goal

Extend client-backed sources and reconcilers to **shows and episodes** — watchlist and
watched/history where each service supports them — building on the movie path proven in Phases 7–8.

## Deliverables

### Source extensions

- Plex/Trakt fetch + apply for TV libraries and episode-level watched state
- Episode-level **Trakt ↔ Plex** watched matching (not just show-level)
- `media_type` handling throughout matcher / mappers for `show` / `episode`
- Letterboxd remains **film-focused** — read-only; no TV write-back
- **TV ratings out of scope** (Letterboxd is ratings SoT and film-only)

### Matching

- `MediaItem.season` / `episode` + composite `match_key` (`tmdb:id:sNeM`)
- `MediaMatcher` indexes by media type + episode S/E (TVDB still in identifier priority)
- Unmatched-items report includes episode-level gaps (`Show S01E02` titles)

### Jobs & UI

- Connections lists movie **and** show libraries; no new job media-type field
- Jobs sync TV when show libraries are selected
- Run summary: `shows_added`, `shows_removed`, `episodes_watched`

## Key files

- `backend/plextraktbox/sync/media_item.py`, `matcher.py`, `engine.py`, `plans.py`
- `backend/plextraktbox/clients/media_mappers.py`, `plex_client.py`, `trakt_client.py`
- `backend/plextraktbox/sync/sources/plex_source.py`, `trakt_source.py`
- Frontend: Connections library picker, RunDetail summary labels, JobForm help text

## Prerequisites

[Phases 7–8](phase-7.md) — **movies working on real data**

## Defers to later phases

| Item | Phase |
| ---- | ----- |
| Global settings, dry-run guards, exclude list | 13 |
| Dashboard ops view, schedule picker | 14 |
| Doppler maintainer workflow | 15 |
| Sync fetch/resolve caches | 21 |
| TrueNAS packaging, GHCR, reverse proxy | 22 |

## Verification

[phase-11-test-plan.md](test-plans/phase-11-test-plan.md)

**Next:** [Phase 12 — CI & quality](phase-12.md) (or product track: [Phase 13](phase-13.md))
