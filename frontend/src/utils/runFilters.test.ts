import { describe, expect, it } from "vitest";
import type { RunListItem } from "../api/jobs";
import { filterRuns, parseRunStatus, parseRunTrigger } from "./runFilters";

const sampleRuns: RunListItem[] = [
  {
    id: 1,
    job_id: 10,
    job_name: "Plex ↔ Trakt",
    trigger: "manual",
    dry_run: true,
    status: "success",
    started_at: "2026-01-01T00:00:00Z",
    finished_at: "2026-01-01T00:00:05Z",
    summary: {},
    error: null,
  },
  {
    id: 2,
    job_id: 11,
    job_name: "Letterboxd → Plex",
    trigger: "scheduled",
    dry_run: false,
    status: "failed",
    started_at: "2026-01-02T00:00:00Z",
    finished_at: "2026-01-02T00:00:10Z",
    summary: {},
    error: "boom",
  },
];

describe("parseRunStatus", () => {
  it("accepts known statuses", () => {
    expect(parseRunStatus("success")).toBe("success");
    expect(parseRunStatus("failed")).toBe("failed");
  });

  it("rejects unknown values", () => {
    expect(parseRunStatus("bogus")).toBeUndefined();
    expect(parseRunStatus(null)).toBeUndefined();
  });
});

describe("parseRunTrigger", () => {
  it("accepts known triggers", () => {
    expect(parseRunTrigger("manual")).toBe("manual");
    expect(parseRunTrigger("scheduled")).toBe("scheduled");
  });

  it("rejects unknown values", () => {
    expect(parseRunTrigger("cron")).toBeUndefined();
    expect(parseRunTrigger(null)).toBeUndefined();
  });
});

describe("filterRuns", () => {
  it("returns all runs when no filters are set", () => {
    expect(filterRuns(sampleRuns, {})).toEqual(sampleRuns);
  });

  it("filters by status and trigger", () => {
    expect(filterRuns(sampleRuns, { status: "success" })).toHaveLength(1);
    expect(filterRuns(sampleRuns, { trigger: "scheduled" })).toHaveLength(1);
    expect(filterRuns(sampleRuns, { status: "success", trigger: "manual" })).toHaveLength(1);
    expect(filterRuns(sampleRuns, { status: "success", trigger: "scheduled" })).toHaveLength(0);
  });
});
