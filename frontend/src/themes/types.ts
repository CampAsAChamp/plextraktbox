import type { MantineThemeOverride } from "@mantine/core"

export type BuiltinThemeId = "one-dark-pro" | "cinema-night" | "nord" | "dracula"

export interface BuiltinThemeDefinition {
  id: BuiltinThemeId
  name: string
  /** Preview swatches in Settings (bg, surface, primary). */
  swatches: [string, string, string]
  theme: MantineThemeOverride
}
