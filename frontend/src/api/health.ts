import { useQuery } from "@tanstack/react-query";
import { api } from "./client";

export interface HealthResponse {
  status: "ok";
  version: string;
  git_sha?: string | null;
  built_at?: string | null;
}

const HEALTH_QUERY_KEY = ["health"] as const;

export function useHealthQuery() {
  return useQuery({
    queryKey: HEALTH_QUERY_KEY,
    queryFn: () => api.get<HealthResponse>("/health"),
    refetchInterval: 60_000,
    refetchIntervalInBackground: true,
  });
}

export function formatVersionLabel(health: HealthResponse | undefined): string {
  if (!health) {
    return "connecting…";
  }
  const sha = health.git_sha?.trim();
  if (sha) {
    return `v${health.version} · ${sha.slice(0, 7)}`;
  }
  return `v${health.version}`;
}
