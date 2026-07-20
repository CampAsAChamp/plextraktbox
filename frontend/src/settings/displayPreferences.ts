export type TimezonePreference = "local" | "utc" | (string & {})
export type TimeFormatPreference = "12h" | "24h"
export type DateFormatPreference = "mdy" | "dmy"
export type YearFormatPreference = "numeric" | "2-digit"
export type TimezoneMode = "local" | "utc" | "manual"

export type DisplayPreferences = {
  timezone: TimezonePreference
  timeFormat: TimeFormatPreference
  dateFormat: DateFormatPreference
  yearFormat: YearFormatPreference
}

export const DEFAULT_DISPLAY_PREFERENCES: DisplayPreferences = {
  timezone: "local",
  timeFormat: "24h",
  dateFormat: "mdy",
  yearFormat: "2-digit",
}

const STORAGE_KEY = "plextraktbox.displayPreferences"

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
] as const

function isTimeFormatPreference(value: unknown): value is TimeFormatPreference {
  return value === "12h" || value === "24h"
}

function isDateFormatPreference(value: unknown): value is DateFormatPreference {
  return value === "mdy" || value === "dmy"
}

function isYearFormatPreference(value: unknown): value is YearFormatPreference {
  return value === "numeric" || value === "2-digit"
}

export function isValidIanaTimezone(value: string): boolean {
  if (value === "UTC") return true
  if (!value.includes("/")) return false

  if (typeof Intl.supportedValuesOf === "function") {
    return Intl.supportedValuesOf("timeZone").includes(value)
  }

  try {
    Intl.DateTimeFormat(undefined, { timeZone: value })
    return true
  } catch {
    return false
  }
}

export function isTimezonePreference(value: unknown): value is TimezonePreference {
  return typeof value === "string" && (value === "local" || value === "utc" || isValidIanaTimezone(value))
}

export function getBrowserTimezone(): string {
  return Intl.DateTimeFormat().resolvedOptions().timeZone ?? "UTC"
}

export function listIanaTimezones(): string[] {
  if (typeof Intl.supportedValuesOf === "function") {
    return Intl.supportedValuesOf("timeZone")
  }
  return [...FALLBACK_TIMEZONES]
}

export function getTimezoneMode(timezone: TimezonePreference): TimezoneMode {
  if (timezone === "local") return "local"
  if (timezone === "utc") return "utc"
  return "manual"
}

export function getManualTimezone(timezone: TimezonePreference): string {
  if (timezone !== "local" && timezone !== "utc") return timezone
  return getBrowserTimezone()
}

export function resolveTimeZone(timezone: TimezonePreference): string | undefined {
  if (timezone === "local") return undefined
  if (timezone === "utc") return "UTC"
  return timezone
}

/** Current UTC offset for an IANA zone, e.g. "UTC-07:00" or "UTC+05:30". */
export function formatTimezoneOffset(timezone: string, at: Date = new Date()): string {
  try {
    const offsetPart = new Intl.DateTimeFormat("en-US", {
      timeZone: timezone,
      timeZoneName: "longOffset",
    })
      .formatToParts(at)
      .find((part) => part.type === "timeZoneName")?.value

    if (!offsetPart || offsetPart === "GMT" || offsetPart === "UTC") {
      return "UTC+00:00"
    }

    // longOffset yields "GMT±HH:mm" (or "GMT±H:mm"); normalize to UTC…
    const match = /^GMT([+-])(\d{1,2})(?::?(\d{2}))?$/.exec(offsetPart)
    if (!match) {
      return offsetPart.replace(/^GMT/, "UTC")
    }

    const sign = match[1]
    const hours = match[2].padStart(2, "0")
    const minutes = match[3] ?? "00"
    return `UTC${sign}${hours}:${minutes}`
  } catch {
    return ""
  }
}

export function formatTimezoneLabel(timezone: string, at: Date = new Date()): string {
  const name = timezone.replace(/_/g, " ")
  const offset = formatTimezoneOffset(timezone, at)
  return offset ? `${name} (${offset})` : name
}

export function normalizeDisplayPreferences(value: unknown): DisplayPreferences {
  if (!value || typeof value !== "object") {
    return DEFAULT_DISPLAY_PREFERENCES
  }

  const record = value as Partial<DisplayPreferences>
  return {
    timezone: isTimezonePreference(record.timezone) ? record.timezone : DEFAULT_DISPLAY_PREFERENCES.timezone,
    timeFormat: isTimeFormatPreference(record.timeFormat) ? record.timeFormat : DEFAULT_DISPLAY_PREFERENCES.timeFormat,
    dateFormat: isDateFormatPreference(record.dateFormat) ? record.dateFormat : DEFAULT_DISPLAY_PREFERENCES.dateFormat,
    yearFormat: isYearFormatPreference(record.yearFormat) ? record.yearFormat : DEFAULT_DISPLAY_PREFERENCES.yearFormat,
  }
}

export function loadDisplayPreferences(): DisplayPreferences {
  if (typeof window === "undefined") {
    return DEFAULT_DISPLAY_PREFERENCES
  }

  try {
    const raw = window.localStorage.getItem(STORAGE_KEY)
    if (!raw) return DEFAULT_DISPLAY_PREFERENCES
    return normalizeDisplayPreferences(JSON.parse(raw))
  } catch {
    return DEFAULT_DISPLAY_PREFERENCES
  }
}

export function saveDisplayPreferences(preferences: DisplayPreferences): void {
  if (typeof window === "undefined") return
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(preferences))
}
