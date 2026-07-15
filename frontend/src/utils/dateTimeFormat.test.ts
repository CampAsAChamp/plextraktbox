import { describe, expect, it } from "vitest";
import {
  formatDateTime,
  formatDuration,
  formatScheduleDateTime,
  formatScheduleDateTimeParts,
  formatTimestamp,
  parseUtcTimestamp,
} from "./dateTimeFormat";

const preferences = {
  timezone: "utc",
  timeFormat: "24h",
  dateFormat: "mdy",
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
    const prefs = { timezone: "local", timeFormat: "12h", dateFormat: "mdy" } as const;
    expect(formatTimestamp(naive, prefs)).toBe(formatTimestamp(explicit, prefs));
  });

  it("formats fixed IANA timezones differently from UTC", () => {
    const value = "2026-07-11T18:30:45.123Z";
    const utc = formatTimestamp(value, preferences);
    const chicago = formatTimestamp(value, {
      timezone: "America/Chicago",
      timeFormat: "24h",
      dateFormat: "mdy",
    });
    expect(chicago).not.toBe(utc);
  });
});

describe("formatDateTime", () => {
  it("returns a dash for missing values", () => {
    expect(formatDateTime(null, preferences)).toBe("—");
  });

  it("formats UTC datetimes in 24-hour time with month-first date", () => {
    const value = "2026-07-11T18:30:45.123Z";
    expect(formatDateTime(value, preferences)).toMatch(/7\/11\/2026/);
    expect(formatDateTime(value, preferences)).toMatch(/18:30:45/);
  });

  it("formats day-first dates when configured", () => {
    const value = "2026-07-11T18:30:45.123Z";
    const formatted = formatDateTime(value, {
      timezone: "utc",
      timeFormat: "24h",
      dateFormat: "dmy",
    });
    expect(formatted).toMatch(/11\/7\/2026/);
    expect(formatted).not.toMatch(/^7\/11\/2026/);
  });

  it("uses 12-hour time when configured", () => {
    const value = "2026-07-11T18:30:45.123Z";
    const formatted = formatDateTime(value, {
      timezone: "utc",
      timeFormat: "12h",
      dateFormat: "mdy",
    });
    expect(formatted).toMatch(/PM|AM/);
  });

  it("formats fixed IANA timezones", () => {
    const value = "2026-07-11T18:30:45.123Z";
    const utc = formatDateTime(value, { timezone: "utc", timeFormat: "24h", dateFormat: "mdy" });
    const chicago = formatDateTime(value, {
      timezone: "America/Chicago",
      timeFormat: "24h",
      dateFormat: "mdy",
    });
    expect(chicago).not.toBe(utc);
  });
});

describe("formatScheduleDateTime", () => {
  it("includes weekday with date and time", () => {
    // Saturday in UTC
    const value = "2026-07-11T18:30:00Z";
    const formatted = formatScheduleDateTime(value, preferences);
    expect(formatted).toMatch(/Sat/);
    expect(formatted).toMatch(/7\/11\/2026/);
    expect(formatted).toMatch(/18:30/);
    expect(formatted).not.toMatch(/18:30:00/);
  });

  it("returns a dash for missing values", () => {
    expect(formatScheduleDateTime(null, preferences)).toBe("—");
  });
});

describe("formatScheduleDateTimeParts", () => {
  it("splits weekday, date, and time into columns", () => {
    const parts = formatScheduleDateTimeParts("2026-07-11T18:30:00Z", preferences);
    expect(parts.weekday).toMatch(/Sat/);
    expect(parts.date).toBe("7/11/2026");
    expect(parts.time).toMatch(/18:30/);
  });

  it("uses day-first date order when configured", () => {
    const parts = formatScheduleDateTimeParts("2026-07-11T18:30:00Z", {
      timezone: "utc",
      timeFormat: "24h",
      dateFormat: "dmy",
    });
    expect(parts.date).toBe("11/7/2026");
  });
});

describe("formatDuration", () => {
  it("returns under one second for short durations", () => {
    expect(formatDuration(0)).toBe("<1 s");
    expect(formatDuration(499)).toBe("<1 s");
  });

  it("formats seconds only", () => {
    expect(formatDuration(1000)).toBe("1 s");
    expect(formatDuration(5000)).toBe("5 s");
  });

  it("formats minutes and seconds", () => {
    expect(formatDuration(7 * 60_000 + 5_000)).toBe("7 min 5 s");
    expect(formatDuration(30 * 60_000)).toBe("30 min");
  });

  it("formats hours, minutes, and seconds", () => {
    expect(formatDuration(3600_000 + 30 * 60_000 + 5_000)).toBe("1 hr 30 min 5 s");
    expect(formatDuration(2 * 3600_000 + 39 * 60_000 + 10_000)).toBe("2 hr 39 min 10 s");
    expect(formatDuration(2 * 3600_000)).toBe("2 hr");
  });
});
