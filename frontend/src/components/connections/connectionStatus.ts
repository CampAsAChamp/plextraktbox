import type { ConnectionSummary, Service } from "src/api/connections";

export const SERVICE_LABELS: Record<Service, string> = {
  plex: "Plex",
  trakt: "Trakt",
  letterboxd: "Letterboxd",
  tmdb: "TMDB",
};

export function statusColor(status: ConnectionSummary["status"]) {
  switch (status) {
    case "ok":
      return "green";
    case "needs_reauth":
      return "orange";
    case "error":
      return "red";
    default:
      return "gray";
  }
}

export function formatConnectionStatus(status: ConnectionSummary["status"]) {
  switch (status) {
    case "ok":
      return "✓";
    case "needs_reauth":
      return "Re-auth";
    case "error":
      return "Error";
    default:
      return "—";
  }
}

export function connectionStatusLabel(status: ConnectionSummary["status"]) {
  switch (status) {
    case "ok":
      return "Connected";
    case "needs_reauth":
      return "Needs re-authorization";
    case "error":
      return "Error";
    default:
      return "Not configured";
  }
}
