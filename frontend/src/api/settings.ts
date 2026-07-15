import { api } from "./client";

export interface ExcludeIds {
  tmdb: string[];
  imdb: string[];
  tvdb: string[];
}

export interface AppSettings {
  default_cron: string;
  cron_timezone: string;
  cron_timezone_resolved: string;
  log_retention_days: number;
  global_dry_run: boolean;
  exclude_ids: ExcludeIds;
  ui_theme: string;
}

export type AppSettingsInput = {
  default_cron: string;
  cron_timezone: string;
  cron_local_zone?: string | null;
  log_retention_days: number;
  global_dry_run: boolean;
  exclude_ids: ExcludeIds;
};

export function getSettings(): Promise<AppSettings> {
  return api.get<AppSettings>("/settings");
}

export function updateSettings(input: AppSettingsInput): Promise<AppSettings> {
  return api.put<AppSettings>("/settings", input);
}

export async function downloadBackup(): Promise<void> {
  const resp = await fetch("/api/settings/backup", {
    method: "GET",
    credentials: "same-origin",
    headers: {
      "X-Requested-With": "XMLHttpRequest",
    },
  });
  if (!resp.ok) {
    throw new Error(`Backup download failed (${resp.status})`);
  }
  const blob = await resp.blob();
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = "plextraktbox-backup.db";
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

export function changePassword(currentPassword: string, newPassword: string): Promise<void> {
  return api.post<void>("/auth/change-password", {
    current_password: currentPassword,
    new_password: newPassword,
  });
}

export function parseExcludeLines(value: string): string[] {
  return value
    .split(/[\n,]+/)
    .map((part) => part.trim())
    .filter(Boolean);
}

export function formatExcludeLines(values: string[] | undefined): string {
  return (values ?? []).join("\n");
}
