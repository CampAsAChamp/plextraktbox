import type { DataType } from "src/api/jobs"

export type SyncService = "plex" | "trakt" | "letterboxd"

export type SourceOfTruthWrite = {
  service: SyncService
  /** Short action suffix, e.g. "add/remove" or "mark watched". */
  action?: string
}

export type SourceOfTruthRule = {
  dataType: DataType
  truth: SyncService
  writes: SourceOfTruthWrite[]
  note?: string
}

export const SOURCE_OF_TRUTH: SourceOfTruthRule[] = [
  {
    dataType: "watchlist",
    truth: "plex",
    writes: [{ service: "trakt", action: "add/remove" }],
    note: "Letterboxd watchlist ignored",
  },
  {
    dataType: "ratings",
    truth: "letterboxd",
    writes: [{ service: "plex" }, { service: "trakt" }],
  },
  {
    dataType: "watched",
    truth: "trakt",
    writes: [{ service: "plex", action: "mark watched" }],
  },
]
