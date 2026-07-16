import type { Service } from "src/api/connections";

/** Brand colors for sync services (text labels and logo fills). */
export const SERVICE_TEXT_COLORS: Record<Exclude<Service, "tmdb">, string> = {
  plex: "#E5A00D",
  trakt: "#9B51E0",
  letterboxd: "#40BCF4",
};
