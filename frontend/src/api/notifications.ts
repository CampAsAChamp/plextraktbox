import { api } from "src/api/client";

export type NotificationChannel = "discord" | "inapp";
export type NotificationScope = "global" | "job";
export type NotifyMode = "inherit" | "custom" | "disabled";
export type InAppLevel = "info" | "success" | "warning" | "error";

export interface NotificationConfig {
  id: number;
  channel: NotificationChannel;
  enabled: boolean;
  on_success: boolean;
  on_failure: boolean;
  scope: NotificationScope;
  job_id: number | null;
  config: Record<string, unknown>;
  has_secret: boolean;
}

export interface DiscordConfigInput {
  webhook_url?: string;
}

export interface NotificationConfigCreateInput {
  channel: NotificationChannel;
  enabled?: boolean;
  on_success?: boolean;
  on_failure?: boolean;
  scope?: NotificationScope;
  job_id?: number | null;
  discord?: DiscordConfigInput;
}

export interface NotificationConfigUpdateInput {
  enabled: boolean;
  on_success: boolean;
  on_failure: boolean;
  discord?: DiscordConfigInput;
}

export interface InAppNotification {
  id: number;
  created_at: string;
  level: InAppLevel;
  title: string;
  body: string;
  read: boolean;
  run_id: number | null;
}

export interface InAppListResponse {
  items: InAppNotification[];
  unread_count: number;
}

export const CHANNEL_LABELS: Record<NotificationChannel, string> = {
  discord: "Discord",
  inapp: "In-app",
};

export const NOTIFY_MODE_LABELS: Record<NotifyMode, string> = {
  inherit: "Use global settings",
  custom: "Custom per-job channels",
  disabled: "Disabled",
};

export function listNotificationConfigs(jobId?: number) {
  const query = jobId != null ? `?job_id=${jobId}` : "";
  return api.get<NotificationConfig[]>(`/notifications/configs${query}`);
}

export function createNotificationConfig(input: NotificationConfigCreateInput) {
  return api.post<NotificationConfig>("/notifications/configs", input);
}

export function updateNotificationConfig(id: number, input: NotificationConfigUpdateInput) {
  return api.put<NotificationConfig>(`/notifications/configs/${id}`, input);
}

export function deleteNotificationConfig(id: number) {
  return api.del<void>(`/notifications/configs/${id}`);
}

export function testNotificationConfig(id: number) {
  return api.post<{ ok: boolean; message: string }>(`/notifications/configs/${id}/test`);
}

export function listInAppNotifications(unreadOnly = false) {
  return api.get<InAppListResponse>(`/notifications/inapp?unread_only=${unreadOnly}`);
}

export function getUnreadCount() {
  return api.get<{ unread_count: number }>("/notifications/inapp/unread-count");
}

export function markInAppRead(id: number) {
  return api.post<InAppNotification>(`/notifications/inapp/${id}/read`);
}

export function markAllInAppRead() {
  return api.post<void>("/notifications/inapp/read-all");
}
