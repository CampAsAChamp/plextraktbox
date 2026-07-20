import { type DateFormatPreference, type DisplayPreferences, resolveTimeZone } from "src/settings/displayPreferences"

const NAIVE_ISO_TIMESTAMP_RE = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?$/

/** API timestamps without a timezone suffix are UTC (SQLite strips tzinfo). */
export function parseUtcTimestamp(value: string): Date {
  if (NAIVE_ISO_TIMESTAMP_RE.test(value)) {
    return new Date(`${value}Z`)
  }
  return new Date(value)
}

function dateTimeOptions(preferences: DisplayPreferences): Intl.DateTimeFormatOptions {
  return {
    timeZone: resolveTimeZone(preferences.timezone),
    hour12: preferences.timeFormat === "12h",
  }
}

function formatDateOrder(month: string, day: string, year: string, dateFormat: DateFormatPreference): string {
  return dateFormat === "dmy" ? `${day}/${month}/${year}` : `${month}/${day}/${year}`
}

function lookupPart(parts: Intl.DateTimeFormatPart[], type: Intl.DateTimeFormatPartTypes): string {
  return parts.find((part) => part.type === type)?.value ?? ""
}

function formatTimeFromParts(parts: Intl.DateTimeFormatPart[], options: { includeSeconds: boolean }): string {
  const hour = lookupPart(parts, "hour")
  const minute = lookupPart(parts, "minute")
  const second = lookupPart(parts, "second")
  const dayPeriod = lookupPart(parts, "dayPeriod")
  const base = options.includeSeconds ? `${hour}:${minute}:${second}` : `${hour}:${minute}`
  return dayPeriod ? `${base} ${dayPeriod}` : base
}

export function formatTimestamp(value: string, preferences: DisplayPreferences): string {
  const date = parseUtcTimestamp(value)
  return date.toLocaleTimeString(undefined, {
    ...dateTimeOptions(preferences),
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    fractionalSecondDigits: 3,
  })
}

export function formatDateTime(value: string | null, preferences: DisplayPreferences): string {
  if (!value) return "—"
  const date = parseUtcTimestamp(value)
  const parts = new Intl.DateTimeFormat(undefined, {
    ...dateTimeOptions(preferences),
    year: preferences.yearFormat,
    month: "numeric",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  }).formatToParts(date)

  const dateText = formatDateOrder(lookupPart(parts, "month"), lookupPart(parts, "day"), lookupPart(parts, "year"), preferences.dateFormat)
  return `${dateText}, ${formatTimeFromParts(parts, { includeSeconds: true })}`
}

/** Schedule fire times: weekday + date + time (no seconds). */
export function formatScheduleDateTime(value: string | null, preferences: DisplayPreferences): string {
  if (!value) return "—"
  const parts = formatScheduleDateTimeParts(value, preferences)
  return `${parts.weekday}, ${parts.date}, ${parts.time}`
}

export interface ScheduleDateTimeParts {
  weekday: string
  date: string
  time: string
}

/** Split a schedule fire time into weekday / date / time for columnar display. */
export function formatScheduleDateTimeParts(value: string, preferences: DisplayPreferences): ScheduleDateTimeParts {
  const date = parseUtcTimestamp(value)
  const parts = new Intl.DateTimeFormat(undefined, {
    ...dateTimeOptions(preferences),
    weekday: "short",
    year: preferences.yearFormat,
    month: "numeric",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).formatToParts(date)

  return {
    weekday: lookupPart(parts, "weekday"),
    date: formatDateOrder(lookupPart(parts, "month"), lookupPart(parts, "day"), lookupPart(parts, "year"), preferences.dateFormat),
    time: formatTimeFromParts(parts, { includeSeconds: false }),
  }
}

/** Formats a millisecond duration as e.g. "7 min 5 s" or "1 hr 30 min 5 s". */
export function formatDuration(ms: number): string {
  if (ms < 1000) return "<1 s"

  const totalSeconds = Math.round(ms / 1000)
  const hours = Math.floor(totalSeconds / 3600)
  const minutes = Math.floor((totalSeconds % 3600) / 60)
  const seconds = totalSeconds % 60

  const parts: string[] = []
  if (hours > 0) parts.push(`${hours} hr`)
  if (minutes > 0) parts.push(`${minutes} min`)
  if (seconds > 0 || parts.length === 0) parts.push(`${seconds} s`)
  return parts.join(" ")
}

const RELATIVE_DIVISIONS: { amount: number; unit: Intl.RelativeTimeFormatUnit }[] = [
  { amount: 60, unit: "second" },
  { amount: 60, unit: "minute" },
  { amount: 24, unit: "hour" },
  { amount: 7, unit: "day" },
  { amount: 4.34524, unit: "week" },
  { amount: 12, unit: "month" },
  { amount: Number.POSITIVE_INFINITY, unit: "year" },
]

/** Relative time like "2h ago" / "in 45m". Returns null for empty/invalid values. */
export function formatRelativeTime(value: string | null, options?: { now?: Date }): string | null {
  if (!value) return null
  const date = parseUtcTimestamp(value)
  if (Number.isNaN(date.getTime())) return null

  const now = options?.now ?? new Date()
  let durationSeconds = (date.getTime() - now.getTime()) / 1000
  const rtf = new Intl.RelativeTimeFormat(undefined, { numeric: "auto" })

  for (const division of RELATIVE_DIVISIONS) {
    if (Math.abs(durationSeconds) < division.amount) {
      return rtf.format(Math.round(durationSeconds), division.unit)
    }
    durationSeconds /= division.amount
  }
  return rtf.format(Math.round(durationSeconds), "year")
}
