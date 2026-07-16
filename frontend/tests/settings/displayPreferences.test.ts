import { afterEach, describe, expect, it } from "vitest"

import {
  DEFAULT_DISPLAY_PREFERENCES,
  formatTimezoneLabel,
  formatTimezoneOffset,
  getTimezoneMode,
  loadDisplayPreferences,
  normalizeDisplayPreferences,
  resolveTimeZone,
  saveDisplayPreferences,
} from "src/settings/displayPreferences"

const STORAGE_KEY = "plextraktbox.displayPreferences"

describe("normalizeDisplayPreferences", () => {
  it("falls back to defaults for invalid values", () => {
    expect(normalizeDisplayPreferences(null)).toEqual(DEFAULT_DISPLAY_PREFERENCES)
    expect(normalizeDisplayPreferences({ timezone: "pst", timeFormat: "military", dateFormat: "ymd" })).toEqual(DEFAULT_DISPLAY_PREFERENCES)
  })

  it("keeps valid values", () => {
    expect(
      normalizeDisplayPreferences({
        timezone: "utc",
        timeFormat: "12h",
        dateFormat: "dmy",
      }),
    ).toEqual({
      timezone: "utc",
      timeFormat: "12h",
      dateFormat: "dmy",
    })
    expect(
      normalizeDisplayPreferences({
        timezone: "America/Chicago",
        timeFormat: "24h",
        dateFormat: "mdy",
      }),
    ).toEqual({
      timezone: "America/Chicago",
      timeFormat: "24h",
      dateFormat: "mdy",
    })
  })

  it("defaults dateFormat when missing from older stored prefs", () => {
    expect(
      normalizeDisplayPreferences({
        timezone: "utc",
        timeFormat: "12h",
      }),
    ).toEqual({
      timezone: "utc",
      timeFormat: "12h",
      dateFormat: "mdy",
    })
  })
})

describe("timezone helpers", () => {
  it("resolves timezone modes", () => {
    expect(getTimezoneMode("local")).toBe("local")
    expect(getTimezoneMode("utc")).toBe("utc")
    expect(getTimezoneMode("America/Chicago")).toBe("manual")
    expect(resolveTimeZone("local")).toBeUndefined()
    expect(resolveTimeZone("utc")).toBe("UTC")
    expect(resolveTimeZone("America/Chicago")).toBe("America/Chicago")
  })

  it("formats UTC offsets for labels", () => {
    // Mid-January avoids DST ambiguity for common zones.
    const winter = new Date("2026-01-15T12:00:00.000Z")
    expect(formatTimezoneOffset("UTC", winter)).toBe("UTC+00:00")
    expect(formatTimezoneOffset("America/Chicago", winter)).toBe("UTC-06:00")
    expect(formatTimezoneOffset("Asia/Kolkata", winter)).toBe("UTC+05:30")
    expect(formatTimezoneLabel("America/Los_Angeles", winter)).toBe("America/Los Angeles (UTC-08:00)")
    expect(formatTimezoneLabel("UTC", winter)).toBe("UTC (UTC+00:00)")
  })
})

describe("display preference storage", () => {
  afterEach(() => {
    window.localStorage.removeItem(STORAGE_KEY)
  })

  it("loads defaults when storage is empty", () => {
    expect(loadDisplayPreferences()).toEqual(DEFAULT_DISPLAY_PREFERENCES)
  })

  it("persists and reloads preferences", () => {
    saveDisplayPreferences({ timezone: "utc", timeFormat: "12h", dateFormat: "dmy" })
    expect(loadDisplayPreferences()).toEqual({
      timezone: "utc",
      timeFormat: "12h",
      dateFormat: "dmy",
    })
  })
})
