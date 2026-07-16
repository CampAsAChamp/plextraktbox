import type { DataType } from "src/api/jobs"

export type SourceOfTruthRule = {
  dataType: DataType
  truth: string
  writes: string
  note?: string
}

export const SOURCE_OF_TRUTH: SourceOfTruthRule[] = [
  {
    dataType: "watchlist",
    truth: "Plex",
    writes: "Trakt add/remove",
    note: "Letterboxd watchlist ignored",
  },
  {
    dataType: "ratings",
    truth: "Letterboxd",
    writes: "Plex + Trakt",
  },
  {
    dataType: "watched",
    truth: "Trakt",
    writes: "Plex mark watched",
  },
]
