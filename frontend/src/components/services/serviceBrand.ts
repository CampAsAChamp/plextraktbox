import type { Service } from "../../api/connections";

/** Text colors for sync services (logo fills may differ, e.g. Trakt icon is red). */
export const SERVICE_TEXT_COLORS: Record<Exclude<Service, "tmdb">, string> = {
  plex: "#E5A00D",
  trakt: "#9B51E0",
  letterboxd: "#40BCF4",
};
