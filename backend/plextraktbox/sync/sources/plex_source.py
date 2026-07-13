"""Plex source adapter (Phase 3: in-memory; Phase 7: client fetch; Phase 8: client apply)."""

from __future__ import annotations

from plextraktbox.sync.sources.memory import MemorySource


class PlexSource(MemorySource):
    def __init__(self) -> None:
        super().__init__(name="plex")
