export type TimezonePreference = "local" | "utc" | (string & {});
export type TimeFormatPreference = "12h" | "24h";
export type TimezoneMode = "local" | "utc" | "fixed";

export type DisplayPreferences = {
  timezone: TimezonePreference;
  timeFormat: TimeFormatPreference;
};

export const DEFAULT_DISPLAY_PREFERENCES: DisplayPreferences = {
  timezone: "local",
  timeFormat: "24h",
};

const STORAGE_KEY = "plextraktbox.displayPreferences";

const FALLBACK_TIMEZONES = [
  "UTC",
  "America/Los_Angeles",
  "America/Denver",
  "America/Chicago",
  "America/New_York",
  "America/Toronto",
  "America/Sao_Paulo",
  "Europe/London",
  "Europe/Berlin",
  "Europe/Paris",
  "Asia/Tokyo",
  "Asia/Shanghai",
  "Asia/Kolkata",
  "Australia/Sydney",
  "Pacific/Auckland",
] as const;

function isTimeFormatPreference(value: unknown): value is TimeFormatPreference {
  return value === "12h" || value === "24h";
}

export function isValidIanaTimezone(value: string): boolean {
  if (value === "UTC") return true;
  if (!value.includes("/")) return false;

  if (typeof Intl.supportedValuesOf === "function") {
    return Intl.supportedValuesOf("timeZone").includes(value);
  }

  try {
    Intl.DateTimeFormat(undefined, { timeZone: value });
    return true;
  } catch {
    return false;
  }
}

export function isTimezonePreference(value: unknown): value is TimezonePreference {
  return typeof value === "string" && (value === "local" || value === "utc" || isValidIanaTimezone(value));
}

export function getBrowserTimezone(): string {
  return Intl.DateTimeFormat().resolvedOptions().timeZone ?? "UTC";
}

export function listIanaTimezones(): string[] {
  if (typeof Intl.supportedValuesOf === "function") {
    return Intl.supportedValuesOf("timeZone");
  }
  return [...FALLBACK_TIMEZONES];
}

export function getTimezoneMode(timezone: TimezonePreference): TimezoneMode {
  if (timezone === "local" || timezone === "utc") return timezone;
  return "fixed";
}

export function getFixedTimezone(timezone: TimezonePreference): string {
  if (timezone !== "local" && timezone !== "utc") return timezone;
  return getBrowserTimezone();
}

export function resolveTimeZone(timezone: TimezonePreference): string | undefined {
  if (timezone === "local") return undefined;
  if (timezone === "utc") return "UTC";
  return timezone;
}

export function formatTimezoneLabel(timezone: string): string {
  return timezone.replace(/_/g, " ");
}

export function normalizeDisplayPreferences(value: unknown): DisplayPreferences {
  if (!value || typeof value !== "object") {
    return DEFAULT_DISPLAY_PREFERENCES;
  }

  const record = value as Partial<DisplayPreferences>;
  return {
    timezone: isTimezonePreference(record.timezone)
      ? record.timezone
      : DEFAULT_DISPLAY_PREFERENCES.timezone,
    timeFormat: isTimeFormatPreference(record.timeFormat)
      ? record.timeFormat
      : DEFAULT_DISPLAY_PREFERENCES.timeFormat,
  };
}

export function loadDisplayPreferences(): DisplayPreferences {
  if (typeof window === "undefined") {
    return DEFAULT_DISPLAY_PREFERENCES;
  }

  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return DEFAULT_DISPLAY_PREFERENCES;
    return normalizeDisplayPreferences(JSON.parse(raw));
  } catch {
    return DEFAULT_DISPLAY_PREFERENCES;
  }
}

export function saveDisplayPreferences(preferences: DisplayPreferences): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(preferences));
}
