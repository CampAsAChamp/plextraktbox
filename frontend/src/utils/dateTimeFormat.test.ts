import { describe, expect, it } from "vitest";
import { formatDateTime, formatTimestamp, parseUtcTimestamp } from "./dateTimeFormat";

const preferences = {
  timezone: "utc",
  timeFormat: "24h",
} as const;

describe("parseUtcTimestamp", () => {
  it("treats naive ISO timestamps as UTC", () => {
    const naive = "2026-07-11T19:31:05.685";
    const explicit = "2026-07-11T19:31:05.685Z";
    expect(parseUtcTimestamp(naive).getTime()).toBe(parseUtcTimestamp(explicit).getTime());
  });
});

describe("formatTimestamp", () => {
  it("formats UTC timestamps in 24-hour time", () => {
    const value = "2026-07-11T18:30:45.123Z";
    expect(formatTimestamp(value, preferences)).toMatch(/18:30:45/);
  });

  it("formats naive UTC timestamps the same as explicit Z timestamps", () => {
    const naive = "2026-07-11T19:31:05.685";
    const explicit = "2026-07-11T19:31:05.685Z";
    const prefs = { timezone: "local", timeFormat: "12h" } as const;
    expect(formatTimestamp(naive, prefs)).toBe(formatTimestamp(explicit, prefs));
  });

  it("formats local and UTC timestamps differently", () => {
    const value = "2026-07-11T18:30:45.123Z";
    expect(formatTimestamp(value, { timezone: "local", timeFormat: "24h" })).not.toBe(
      formatTimestamp(value, preferences),
    );
  });
});

describe("formatDateTime", () => {
  it("returns a dash for missing values", () => {
    expect(formatDateTime(null, preferences)).toBe("—");
  });

  it("formats UTC datetimes in 24-hour time", () => {
    const value = "2026-07-11T18:30:45.123Z";
    expect(formatDateTime(value, preferences)).toMatch(/7\/11\/2026/);
    expect(formatDateTime(value, preferences)).toMatch(/18:30:45/);
  });

  it("uses 12-hour time when configured", () => {
    const value = "2026-07-11T18:30:45.123Z";
    const formatted = formatDateTime(value, { timezone: "utc", timeFormat: "12h" });
    expect(formatted).toMatch(/PM|AM/);
  });

  it("formats fixed IANA timezones", () => {
    const value = "2026-07-11T18:30:45.123Z";
    const utc = formatDateTime(value, { timezone: "utc", timeFormat: "24h" });
    const chicago = formatDateTime(value, { timezone: "America/Chicago", timeFormat: "24h" });
    expect(chicago).not.toBe(utc);
  });
});
