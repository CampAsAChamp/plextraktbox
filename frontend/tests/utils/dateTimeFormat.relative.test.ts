import { describe, expect, it } from "vitest"

import { formatRelativeTime } from "src/utils/dateTimeFormat"

describe("formatRelativeTime", () => {
  it("formats past times", () => {
    const now = new Date("2026-07-16T12:00:00.000Z")
    expect(formatRelativeTime("2026-07-16T11:00:00.000Z", { now })).toMatch(/hour/i)
    expect(formatRelativeTime("2026-07-16T11:58:00.000Z", { now })).toMatch(/minute/i)
  })

  it("formats future times", () => {
    const now = new Date("2026-07-16T12:00:00.000Z")
    expect(formatRelativeTime("2026-07-16T12:45:00.000Z", { now })).toMatch(/minute/i)
  })

  it("returns null for empty values", () => {
    expect(formatRelativeTime(null)).toBeNull()
  })
})
