"""Trakt source adapter (Phase 3: in-memory backing; client fetch in a later phase)."""

from __future__ import annotations

from plextraktbox.sync.sources.memory import MemorySource


class TraktSource(MemorySource):
    def __init__(self) -> None:
        super().__init__(name="trakt")
