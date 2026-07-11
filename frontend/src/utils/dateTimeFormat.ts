import { resolveTimeZone, type DisplayPreferences } from "../settings/displayPreferences";

const NAIVE_ISO_TIMESTAMP_RE = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?$/;

/** API timestamps without a timezone suffix are UTC (SQLite strips tzinfo). */
export function parseUtcTimestamp(value: string): Date {
  if (NAIVE_ISO_TIMESTAMP_RE.test(value)) {
    return new Date(`${value}Z`);
  }
  return new Date(value);
}

function dateTimeOptions(preferences: DisplayPreferences): Intl.DateTimeFormatOptions {
  return {
    timeZone: resolveTimeZone(preferences.timezone),
    hour12: preferences.timeFormat === "12h",
  };
}

export function formatTimestamp(value: string, preferences: DisplayPreferences): string {
  const date = parseUtcTimestamp(value);
  return date.toLocaleTimeString(undefined, {
    ...dateTimeOptions(preferences),
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    fractionalSecondDigits: 3,
  });
}

export function formatDateTime(value: string | null, preferences: DisplayPreferences): string {
  if (!value) return "—";
  const date = parseUtcTimestamp(value);
  return date.toLocaleString(undefined, {
    ...dateTimeOptions(preferences),
    year: "numeric",
    month: "numeric",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}
