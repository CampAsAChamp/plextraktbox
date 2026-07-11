import { api } from "./client";
import type { RunListResponse } from "./jobs";

export function listRuns(params?: { job_id?: number; limit?: number; offset?: number }) {
  const search = new URLSearchParams();
  if (params?.job_id !== undefined) search.set("job_id", String(params.job_id));
  if (params?.limit !== undefined) search.set("limit", String(params.limit));
  if (params?.offset !== undefined) search.set("offset", String(params.offset));
  const query = search.toString();
  return api.get<RunListResponse>(`/runs${query ? `?${query}` : ""}`);
}

export function getRun(id: number) {
  return api.get<RunListResponse["items"][number]>(`/runs/${id}`);
}
