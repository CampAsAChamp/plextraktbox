import type { components } from "src/api/generated/schema"

type Schemas = components["schemas"]

export type SourcePair = Schemas["SourcePair"]
export type DataType = Schemas["DataType"]
export type NotifyMode = Schemas["NotifyMode"]
export type ExcludeIds = Schemas["ExcludeIds"]
export type JobRunStatus = Schemas["JobRunStatus"]
export type JobLastRun = Schemas["JobLastRun"]
/** UI-facing alias for JobResponse. */
export type Job = Schemas["JobResponse"]
export type SchedulePreview = Schemas["SchedulePreviewResponse"]
export type JobInput = Schemas["JobCreateRequest"]
export type RunTrigger = Schemas["RunTrigger"]
export type JobRun = Schemas["JobRunResponse"]
export type RunListResponse = Schemas["RunListResponse"]
export type RunListItem = RunListResponse["items"][number]

export const SOURCE_PAIR_LABELS: Record<SourcePair, string> = {
  plex_trakt: "Plex ↔ Trakt",
  letterboxd_plex: "Letterboxd → Plex",
  letterboxd_trakt: "Letterboxd → Trakt",
}

export const DATA_TYPE_LABELS: Record<DataType, string> = {
  watchlist: "Watchlist",
  ratings: "Ratings",
  watched: "Watched history",
}

export const DATA_TYPE_COLORS: Record<DataType, string> = {
  watchlist: "cyan",
  ratings: "yellow",
  watched: "teal",
}

export const DATA_TYPES_BY_PAIR: Record<SourcePair, DataType[]> = {
  plex_trakt: ["watchlist", "watched"],
  letterboxd_plex: ["ratings"],
  letterboxd_trakt: ["ratings", "watched"],
}
