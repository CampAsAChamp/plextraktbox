# Rename — `media-sync` → `plextraktbox`

**Status:** Done

## Goal

Align the repository, Python package, environment variable prefix, Docker image name, and documentation
with the final product name **plextraktbox**.

## Deliverables

- Python package and import path renamed to `plextraktbox`
- Environment/config prefix updated (e.g. `PLEXTRAKTBOX_*` where applicable)
- Docker image, compose service names, and CI references updated
- Docs and README use the new name throughout

## Notes

This was a one-time migration between Phase 0 and Phase 1. No separate test plan — covered by
existing Phase 0 smoke tests and CI.

**Next:** [Phase 1 — Auth + wizard](phase-1.md)
