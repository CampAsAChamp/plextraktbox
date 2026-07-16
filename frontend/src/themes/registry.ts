import { cinemaNightDefinition } from "src/themes/cinema-night";
import { draculaDefinition } from "src/themes/dracula";
import { nordDefinition } from "src/themes/nord";
import { oneDarkProDefinition, oneDarkProTheme } from "src/themes/one-dark-pro";
import type { BuiltinThemeDefinition, BuiltinThemeId } from "src/themes/types";

export const DEFAULT_THEME_ID: BuiltinThemeId = "one-dark-pro";

export const BUILTIN_THEMES: BuiltinThemeDefinition[] = [
  oneDarkProDefinition,
  cinemaNightDefinition,
  nordDefinition,
  draculaDefinition,
];

const BY_ID = Object.fromEntries(BUILTIN_THEMES.map((t) => [t.id, t])) as Record<
  BuiltinThemeId,
  BuiltinThemeDefinition
>;

export function isBuiltinThemeId(id: string): id is BuiltinThemeId {
  return id in BY_ID;
}

export function getBuiltinTheme(id: string): BuiltinThemeDefinition | undefined {
  return isBuiltinThemeId(id) ? BY_ID[id] : undefined;
}

/** Neutral dark base used when a custom CSS theme is active. */
export const customThemeBase = oneDarkProTheme;

export type { BuiltinThemeDefinition, BuiltinThemeId };
