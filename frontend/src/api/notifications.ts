import { api } from "src/api/client"
import type { components } from "src/api/generated/schema"

type Schemas = components["schemas"]

export type NotificationChannel = Schemas["NotificationChannel"]
export type NotificationScope = Schemas["NotificationScope"]
export type NotifyMode = Schemas["NotifyMode"]
export type InAppLevel = Schemas["InAppLevel"]
export type NotificationConfig = Schemas["NotificationConfigResponse"]
export type DiscordConfigInput = Schemas["DiscordConfigInput"]
export type NotificationConfigCreateInput = Schemas["NotificationConfigCreateRequest"]
export type NotificationConfigUpdateInput = Schemas["NotificationConfigUpdateRequest"]
export type InAppNotification = Schemas["InAppNotificationResponse"]
export type InAppListResponse = Schemas["InAppListResponse"]

export const CHANNEL_LABELS: Record<NotificationChannel, string> = {
  discord: "Discord",
  inapp: "In-app",
}

export const NOTIFY_MODE_LABELS: Record<NotifyMode, string> = {
  inherit: "Use global settings",
  custom: "Custom per-job channels",
  disabled: "Disabled",
}

export function listNotificationConfigs(jobId?: number) {
  const query = jobId != null ? `?job_id=${jobId}` : ""
  return api.get<NotificationConfig[]>(`/notifications/configs${query}`)
}

export function createNotificationConfig(input: NotificationConfigCreateInput) {
  return api.post<NotificationConfig>("/notifications/configs", input)
}

export function updateNotificationConfig(id: number, input: NotificationConfigUpdateInput) {
  return api.put<NotificationConfig>(`/notifications/configs/${id}`, input)
}

export function deleteNotificationConfig(id: number) {
  return api.del<void>(`/notifications/configs/${id}`)
}

export function testNotificationConfig(id: number) {
  return api.post<Schemas["NotificationTestResponse"]>(`/notifications/configs/${id}/test`)
}

export function listInAppNotifications(unreadOnly = false) {
  return api.get<InAppListResponse>(`/notifications/inapp?unread_only=${unreadOnly}`)
}

export function getUnreadCount() {
  return api.get<Schemas["UnreadCountResponse"]>("/notifications/inapp/unread-count")
}

export function markInAppRead(id: number) {
  return api.post<InAppNotification>(`/notifications/inapp/${id}/read`)
}

export function markAllInAppRead() {
  return api.post<void>("/notifications/inapp/read-all")
}

export function deleteInAppNotification(id: number) {
  return api.del<void>(`/notifications/inapp/${id}`)
}

export function clearAllInAppNotifications() {
  return api.del<void>("/notifications/inapp/clear-all")
}

/** Local ENV only — 404 when the backend is not ENV=local. */
export function isLocalDevApi() {
  return api
    .get<{ started_at: number }>("/dev/revision")
    .then((data) => typeof data.started_at === "number")
    .catch(() => false)
}

/** Local ENV only — inserts sample in-app notifications for UI testing. */
export function seedDevInAppNotifications() {
  return api.post<InAppListResponse>("/dev/notifications/seed")
}
