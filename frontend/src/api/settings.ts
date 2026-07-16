import { api } from "src/api/client"
import type { components } from "src/api/generated/schema"

type Schemas = components["schemas"]

export type ExcludeIds = Schemas["ExcludeIds"]
export type AppSettings = Schemas["SettingsResponse"]
export type AppSettingsInput = Schemas["SettingsUpdateRequest"]
/** Request body fields are optional so callers can clear subsets (defaults apply). */
export type ClearSyncCachesInput = Partial<Schemas["ClearSyncCachesRequest"]>
export type ClearSyncCachesResult = Schemas["ClearSyncCachesResponse"]

export function getSettings(): Promise<AppSettings> {
  return api.get<AppSettings>("/settings")
}

export function updateSettings(input: AppSettingsInput): Promise<AppSettings> {
  return api.put<AppSettings>("/settings", input)
}

export function clearSyncCaches(input: ClearSyncCachesInput = {}): Promise<ClearSyncCachesResult> {
  return api.post<ClearSyncCachesResult>("/settings/clear-sync-caches", {
    letterboxd_export: input.letterboxd_export ?? true,
    letterboxd_slug: input.letterboxd_slug ?? true,
    trakt_lists: input.trakt_lists ?? true,
    discover_keys: input.discover_keys ?? true,
  })
}

export async function downloadBackup(): Promise<void> {
  const resp = await fetch("/api/settings/backup", {
    method: "GET",
    credentials: "same-origin",
    headers: {
      "X-Requested-With": "XMLHttpRequest",
    },
  })
  if (!resp.ok) {
    throw new Error(`Backup download failed (${resp.status})`)
  }
  const blob = await resp.blob()
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement("a")
  anchor.href = url
  anchor.download = "plextraktbox-backup.db"
  document.body.appendChild(anchor)
  anchor.click()
  anchor.remove()
  URL.revokeObjectURL(url)
}

export async function restoreBackup(file: File): Promise<{ ok: boolean; message: string }> {
  const body = new FormData()
  body.append("file", file)
  const resp = await fetch("/api/settings/backup/restore", {
    method: "POST",
    credentials: "same-origin",
    headers: {
      "X-Requested-With": "XMLHttpRequest",
    },
    body,
  })
  if (!resp.ok) {
    let detail = `Restore failed (${resp.status})`
    try {
      const payload = (await resp.json()) as { detail?: unknown }
      if (typeof payload.detail === "string") {
        detail = payload.detail
      }
    } catch {
      // keep status message
    }
    throw new Error(detail)
  }
  return resp.json() as Promise<{ ok: boolean; message: string }>
}

export function changePassword(currentPassword: string, newPassword: string): Promise<void> {
  return api.post<void>("/auth/change-password", {
    current_password: currentPassword,
    new_password: newPassword,
  })
}

export function parseExcludeLines(value: string): string[] {
  return value
    .split(/[\n,]+/)
    .map((part) => part.trim())
    .filter(Boolean)
}

export function formatExcludeLines(values: string[] | undefined): string {
  return (values ?? []).join("\n")
}
