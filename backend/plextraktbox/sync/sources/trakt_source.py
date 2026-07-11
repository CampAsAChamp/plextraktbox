"""Trakt source adapter (Phase 3: in-memory backing; Phase 7: client fetch/apply)."""

from __future__ import annotations

from plextraktbox.sync.sources.memory import MemorySource


class TraktSource(MemorySource):
    def __init__(self) -> None:
        super().__init__(name="trakt")
