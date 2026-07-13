export type Service = "plex" | "trakt" | "letterboxd" | "tmdb";

export type ConnectionStatus =
  | "ok"
  | "unconfigured"
  | "needs_reauth"
  | "error";

export interface ConnectionSummary {
  service: Service;
  status: ConnectionStatus;
  config: Record<string, unknown>;
  token_expires_at: string | null;
}

export interface ConnectionsStatus {
  needs_connections: boolean;
  connections: ConnectionSummary[];
}

export interface ConnectionTestResult {
  ok: boolean;
  message: string;
  details?: Record<string, string>;
}

export interface PlexConnectionInput {
  url: string;
  token: string;
}

export interface PlexPinStart {
  pin_id: number;
  pin_code: string;
  auth_url: string;
  verification_url: string;
  expires_in: number;
  interval: number;
}

export interface PlexPinPollInput {
  pin_id: number;
  pin_code: string;
}

export interface PlexPinPollResult {
  status: "pending" | "ok";
  connection: ConnectionSummary | null;
}

export interface LetterboxdConnectionInput {
  username: string;
  password?: string;
}

export interface TmdbConnectionInput {
  api_key: string;
}

export interface TraktDeviceStart {
  user_code: string;
  device_code: string;
  verification_url: string;
  expires_in: number;
  interval: number;
}

export interface TraktDevicePollInput {
  device_code: string;
}

export interface TraktDevicePollResult {
  status: "pending" | "ok";
  connection: ConnectionSummary | null;
}

export interface PlexLibraryInfo {
  id: string;
  title: string;
  type: string;
}

export interface PlexLibrariesResponse {
  libraries: PlexLibraryInfo[];
  selected_ids: string[];
}
