import { api } from "src/api/client"
import type { components } from "src/api/generated/schema"

type Schemas = components["schemas"]

export type ThemeInfo = Schemas["ThemeInfoResponse"]
export type ThemeActive = Schemas["ThemeActiveResponse"]

export function listThemes(): Promise<ThemeInfo[]> {
  return api.get<ThemeInfo[]>("/themes")
}

export function uploadTheme(css: string, filename?: string): Promise<ThemeInfo> {
  return api.post<ThemeInfo>("/themes", { css, filename: filename ?? null })
}

export function deleteTheme(themeId: string): Promise<void> {
  return api.del<void>(`/themes/${encodeURIComponent(themeId)}`)
}

export function fetchThemeCss(themeId: string): Promise<string> {
  return api.getText(`/themes/${encodeURIComponent(themeId)}/css`)
}

export function updateActiveTheme(themeId: string): Promise<ThemeActive> {
  return api.put<ThemeActive>("/settings/theme", { theme_id: themeId })
}
