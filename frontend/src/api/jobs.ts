export type SourcePair =
  | "plex_trakt"
  | "letterboxd_plex"
  | "letterboxd_trakt";

export type DataType = "watchlist" | "ratings" | "watched";

export type NotifyMode = "inherit" | "custom" | "disabled";

export interface ExcludeIds {
  tmdb: string[];
  imdb: string[];
  tvdb: string[];
}

export type JobRunStatus = "running" | "success" | "failed" | "partial";

export interface JobLastRun {
  id: number;
  status: JobRunStatus;
  dry_run: boolean;
  started_at: string;
  finished_at: string | null;
  matched: number;
  added: number;
  errors: number;
}

export interface Job {
  id: number;
  name: string;
  source_pair: SourcePair;
  enabled: boolean;
  cron: string;
  dry_run: boolean;
  require_dry_run_first: boolean;
  data_types: DataType[];
  notify_mode: NotifyMode;
  exclude_ids: ExcludeIds;
  /** Next scheduled fire time (ISO UTC), null when disabled or unscheduled. */
  next_run_at: string | null;
  /** Most recent run snapshot, null when the job has never run. */
  last_run: JobLastRun | null;
}

export interface SchedulePreview {
  times: string[];
}

export interface JobInput {
  name: string;
  source_pair: SourcePair;
  enabled: boolean;
  cron: string;
  dry_run: boolean;
  require_dry_run_first: boolean;
  data_types: DataType[];
  notify_mode: NotifyMode;
  exclude_ids: ExcludeIds;
}

export type RunTrigger = "scheduled" | "manual";

export interface JobRun {
  id: number;
  job_id: number;
  trigger: RunTrigger;
  dry_run: boolean;
  status: JobRunStatus;
  started_at: string;
  finished_at: string | null;
  summary: Record<string, number>;
  error: string | null;
}

export interface RunListItem extends JobRun {
  job_name: string | null;
  source_pair: SourcePair | null;
}

export interface RunListResponse {
  items: RunListItem[];
  limit: number;
  offset: number;
}

export const SOURCE_PAIR_LABELS: Record<SourcePair, string> = {
  plex_trakt: "Plex ↔ Trakt",
  letterboxd_plex: "Letterboxd → Plex",
  letterboxd_trakt: "Letterboxd → Trakt",
};

export const DATA_TYPE_LABELS: Record<DataType, string> = {
  watchlist: "Watchlist",
  ratings: "Ratings",
  watched: "Watched history",
};

export const DATA_TYPE_COLORS: Record<DataType, string> = {
  watchlist: "cyan",
  ratings: "yellow",
  watched: "teal",
};

export const DATA_TYPES_BY_PAIR: Record<SourcePair, DataType[]> = {
  plex_trakt: ["watchlist", "watched"],
  letterboxd_plex: ["ratings"],
  letterboxd_trakt: ["ratings", "watched"],
};
