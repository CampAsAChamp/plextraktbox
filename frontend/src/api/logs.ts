import { api } from "./client";

export type LogEntry = {
  id: number;
  run_id: number;
  ts: string;
  level: string;
  logger: string;
  message: string;
  context: Record<string, unknown>;
};

export type LogListResponse = {
  items: LogEntry[];
  limit: number;
  after_id: number;
};

export type StreamLogPayload = LogEntry & { type: "log" };
export type StreamEndPayload = { type: "end"; status: string };
export type StreamPayload = StreamLogPayload | StreamEndPayload;

export function listRunLogs(
  runId: number,
  params?: { after_id?: number; limit?: number; level?: string; search?: string },
) {
  const search = new URLSearchParams();
  if (params?.after_id !== undefined) search.set("after_id", String(params.after_id));
  if (params?.limit !== undefined) search.set("limit", String(params.limit));
  if (params?.level) search.set("level", params.level);
  if (params?.search) search.set("search", params.search);
  const query = search.toString();
  return api.get<LogListResponse>(`/runs/${runId}/logs${query ? `?${query}` : ""}`);
}

export function runLogsStreamUrl(runId: number, afterId = 0) {
  const search = new URLSearchParams();
  if (afterId > 0) search.set("after_id", String(afterId));
  const query = search.toString();
  return `/api/runs/${runId}/logs/stream${query ? `?${query}` : ""}`;
}

export type LogExportFormat = "txt" | "jsonl";

export async function downloadRunLogs(runId: number, format: LogExportFormat): Promise<void> {
  const resp = await fetch(`/api/runs/${runId}/logs/export?format=${format}`, {
    method: "GET",
    credentials: "same-origin",
    headers: {
      "X-Requested-With": "XMLHttpRequest",
    },
  });
  if (!resp.ok) {
    throw new Error(`Log export failed (${resp.status})`);
  }
  const blob = await resp.blob();
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `run-${runId}-logs.${format}`;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}
