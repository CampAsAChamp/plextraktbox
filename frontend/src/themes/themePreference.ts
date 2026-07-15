import { DEFAULT_THEME_ID } from "./registry";

const STORAGE_KEY = "plextraktbox.uiTheme";

export function readCachedThemeId(): string {
  try {
    const value = localStorage.getItem(STORAGE_KEY);
    if (value && value.trim()) {
      return value.trim();
    }
  } catch {
    // ignore (private mode / SSR)
  }
  return DEFAULT_THEME_ID;
}

export function writeCachedThemeId(themeId: string): void {
  try {
    localStorage.setItem(STORAGE_KEY, themeId);
  } catch {
    // ignore
  }
}
