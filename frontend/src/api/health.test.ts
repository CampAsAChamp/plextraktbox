import { describe, expect, it } from "vitest"

import { formatVersionLabel } from "src/api/health"

const baseHealth = {
  status: "ok" as const,
  version: "1.2.3",
  db_writable: true,
  scheduler_running: true,
  connections: {},
}

describe("formatVersionLabel", () => {
  it("includes version only when git sha is absent", () => {
    expect(formatVersionLabel(baseHealth)).toBe("v1.2.3")
  })

  it("includes short git sha when present", () => {
    expect(formatVersionLabel({ ...baseHealth, git_sha: "abcdef123456" })).toBe("v1.2.3 · abcdef1")
  })

  it("shows connecting when health is undefined", () => {
    expect(formatVersionLabel(undefined)).toBe("connecting…")
  })
})
