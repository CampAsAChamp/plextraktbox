import { describe, expect, it } from "vitest"

import type { Job } from "src/api/jobs"
import type { RunListItem } from "src/api/runs"
import { aggregateGlanceStats } from "src/utils/runGlanceStats"

function run(partial: Partial<RunListItem> & Pick<RunListItem, "id" | "status" | "started_at">): RunListItem {
  return {
    job_id: 1,
    job_name: "Test",
    source_pair: "plex_trakt",
    trigger: "manual",
    dry_run: false,
    finished_at: partial.started_at,
    summary: { planned: 3, matched: 0, added: 0, removed: 0, rated: 0, watched: 0, skipped: 0, errors: 0 },
    error: null,
    ...partial,
  } as RunListItem
}

describe("aggregateGlanceStats", () => {
  const now = new Date("2026-07-16T12:00:00.000Z")

  it("counts runs in the window and sums planned", () => {
    const jobs = [{ id: 1, enabled: true, next_run_at: "2026-07-16T15:00:00.000Z" } as Job]
    const runs = [
      run({ id: 1, status: "success", started_at: "2026-07-16T10:00:00.000Z" }),
      run({ id: 2, status: "failed", started_at: "2026-07-16T11:00:00.000Z" }),
      run({ id: 3, status: "success", started_at: "2026-07-10T10:00:00.000Z" }),
    ]
    const stats = aggregateGlanceStats(jobs, runs, "24h", now)
    expect(stats.success).toBe(1)
    expect(stats.failed).toBe(1)
    expect(stats.planned).toBe(6)
    expect(stats.nextRunAt).toBe("2026-07-16T15:00:00.000Z")
  })
})
