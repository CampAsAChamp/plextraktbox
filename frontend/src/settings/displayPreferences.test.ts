import { afterEach, describe, expect, it } from "vitest";
import {
  DEFAULT_DISPLAY_PREFERENCES,
  getTimezoneMode,
  loadDisplayPreferences,
  normalizeDisplayPreferences,
  resolveTimeZone,
  saveDisplayPreferences,
} from "./displayPreferences";

const STORAGE_KEY = "plextraktbox.displayPreferences";

describe("normalizeDisplayPreferences", () => {
  it("falls back to defaults for invalid values", () => {
    expect(normalizeDisplayPreferences(null)).toEqual(DEFAULT_DISPLAY_PREFERENCES);
    expect(
      normalizeDisplayPreferences({ timezone: "pst", timeFormat: "military", dateFormat: "ymd" }),
    ).toEqual(DEFAULT_DISPLAY_PREFERENCES);
  });

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
    });
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
    });
  });

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
    });
  });
});

describe("timezone helpers", () => {
  it("resolves timezone modes", () => {
    expect(getTimezoneMode("local")).toBe("local");
    expect(getTimezoneMode("utc")).toBe("utc");
    expect(getTimezoneMode("America/Chicago")).toBe("fixed");
    expect(resolveTimeZone("local")).toBeUndefined();
    expect(resolveTimeZone("utc")).toBe("UTC");
    expect(resolveTimeZone("America/Chicago")).toBe("America/Chicago");
  });
});

describe("display preference storage", () => {
  afterEach(() => {
    window.localStorage.removeItem(STORAGE_KEY);
  });

  it("loads defaults when storage is empty", () => {
    expect(loadDisplayPreferences()).toEqual(DEFAULT_DISPLAY_PREFERENCES);
  });

  it("persists and reloads preferences", () => {
    saveDisplayPreferences({ timezone: "utc", timeFormat: "12h", dateFormat: "dmy" });
    expect(loadDisplayPreferences()).toEqual({
      timezone: "utc",
      timeFormat: "12h",
      dateFormat: "dmy",
    });
  });
});
