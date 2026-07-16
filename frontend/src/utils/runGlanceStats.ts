import type { Job } from "src/api/jobs"
import type { RunListItem } from "src/api/runs"
import { parseUtcTimestamp } from "src/utils/dateTimeFormat"

export type GlanceWindow = "24h" | "7d"

export type GlanceStats = {
  success: number
  failed: number
  partial: number
  running: number
  planned: number
  nextRunAt: string | null
}

function windowMs(window: GlanceWindow): number {
  return window === "24h" ? 24 * 60 * 60 * 1000 : 7 * 24 * 60 * 60 * 1000
}

function runTimeMs(run: RunListItem): number {
  return parseUtcTimestamp(run.finished_at ?? run.started_at).getTime()
}

export function filterRunsInWindow(runs: RunListItem[], window: GlanceWindow, now = new Date()): RunListItem[] {
  const cutoff = now.getTime() - windowMs(window)
  return runs.filter((run) => runTimeMs(run) >= cutoff)
}

export function aggregateGlanceStats(jobs: Job[], runs: RunListItem[], window: GlanceWindow, now = new Date()): GlanceStats {
  const inWindow = filterRunsInWindow(runs, window, now)
  let success = 0
  let failed = 0
  let partial = 0
  let running = 0
  let planned = 0

  for (const run of inWindow) {
    if (run.status === "success") success += 1
    else if (run.status === "failed") failed += 1
    else if (run.status === "partial") partial += 1
    else if (run.status === "running") running += 1
    planned += typeof run.summary?.planned === "number" ? run.summary.planned : 0
  }

  const nextTimes = jobs
    .filter((job) => job.enabled && job.next_run_at)
    .map((job) => job.next_run_at as string)
    .sort()

  return {
    success,
    failed,
    partial,
    running,
    planned,
    nextRunAt: nextTimes[0] ?? null,
  }
}
