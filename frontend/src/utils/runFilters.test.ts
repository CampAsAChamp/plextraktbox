import { describe, expect, it } from "vitest";
import type { RunListItem } from "../api/jobs";
import { filterRuns, parseRunStatuses, parseRunTrigger } from "./runFilters";

const sampleRuns: RunListItem[] = [
  {
    id: 1,
    job_id: 10,
    job_name: "Plex ↔ Trakt",
    source_pair: "plex_trakt",
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
    source_pair: "letterboxd_plex",
    trigger: "scheduled",
    dry_run: false,
    status: "failed",
    started_at: "2026-01-02T00:00:00Z",
    finished_at: "2026-01-02T00:00:10Z",
    summary: {},
    error: "boom",
  },
];

describe("parseRunStatuses", () => {
  it("accepts known statuses", () => {
    expect(parseRunStatuses("success")).toEqual(["success"]);
    expect(parseRunStatuses("failed,partial")).toEqual(["failed", "partial"]);
  });

  it("rejects unknown values", () => {
    expect(parseRunStatuses("bogus")).toEqual([]);
    expect(parseRunStatuses("failed,bogus,partial")).toEqual(["failed", "partial"]);
    expect(parseRunStatuses(null)).toEqual([]);
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
    expect(filterRuns(sampleRuns, { statuses: ["success"] })).toHaveLength(1);
    expect(filterRuns(sampleRuns, { statuses: ["failed", "success"] })).toHaveLength(2);
    expect(filterRuns(sampleRuns, { trigger: "scheduled" })).toHaveLength(1);
    expect(filterRuns(sampleRuns, { statuses: ["success"], trigger: "manual" })).toHaveLength(1);
    expect(filterRuns(sampleRuns, { statuses: ["success"], trigger: "scheduled" })).toHaveLength(0);
  });
});
