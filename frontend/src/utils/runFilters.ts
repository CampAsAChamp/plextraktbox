import type { JobRunStatus, RunListItem, RunTrigger } from "../api/jobs";

export const RUN_STATUS_OPTIONS: { value: JobRunStatus; label: string }[] = [
  { value: "running", label: "Running" },
  { value: "success", label: "Success" },
  { value: "partial", label: "Partial" },
  { value: "failed", label: "Failed" },
];

export const RUN_TRIGGER_OPTIONS: { value: RunTrigger; label: string }[] = [
  { value: "manual", label: "Manual" },
  { value: "scheduled", label: "Scheduled" },
];

const RUN_STATUSES = new Set<JobRunStatus>(RUN_STATUS_OPTIONS.map((option) => option.value));
const RUN_TRIGGERS = new Set<RunTrigger>(RUN_TRIGGER_OPTIONS.map((option) => option.value));

export function parseRunStatuses(value: string | null): JobRunStatus[] {
  if (!value) {
    return [];
  }
  return value
    .split(",")
    .map((part) => part.trim())
    .filter((part): part is JobRunStatus => RUN_STATUSES.has(part as JobRunStatus));
}

export function parseRunTrigger(value: string | null): RunTrigger | undefined {
  if (value && RUN_TRIGGERS.has(value as RunTrigger)) {
    return value as RunTrigger;
  }
  return undefined;
}

export function filterRuns(
  items: RunListItem[],
  filters: { statuses?: JobRunStatus[]; trigger?: RunTrigger },
): RunListItem[] {
  const statusFilter = filters.statuses?.length ? new Set(filters.statuses) : null;
  return items.filter((run) => {
    if (statusFilter && !statusFilter.has(run.status)) {
      return false;
    }
    if (filters.trigger && run.trigger !== filters.trigger) {
      return false;
    }
    return true;
  });
}
