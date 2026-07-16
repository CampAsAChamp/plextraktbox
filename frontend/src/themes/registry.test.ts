import { describe, expect, it } from "vitest"

import { BUILTIN_THEMES, DEFAULT_THEME_ID, getBuiltinTheme, isBuiltinThemeId } from "src/themes/registry"

describe("theme registry", () => {
  it("defaults to Atom One Dark Pro", () => {
    expect(DEFAULT_THEME_ID).toBe("one-dark-pro")
    expect(getBuiltinTheme(DEFAULT_THEME_ID)?.name).toBe("Atom One Dark Pro")
  })

  it("exposes four built-ins with primary colors", () => {
    expect(BUILTIN_THEMES.map((t) => t.id)).toEqual(["one-dark-pro", "cinema-night", "nord", "dracula"])
    for (const def of BUILTIN_THEMES) {
      expect(def.theme.primaryColor).toBeTruthy()
      expect(def.swatches).toHaveLength(3)
    }
  })

  it("narrows builtin ids", () => {
    expect(isBuiltinThemeId("nord")).toBe(true)
    expect(isBuiltinThemeId("ocean-night")).toBe(false)
  })
})
