import type { JobRunStatus, RunListItem, RunTrigger } from "../api/jobs";

export const RUN_STATUS_OPTIONS: { value: JobRunStatus; label: string }[] = [
  { value: "running", label: "Running" },
  { value: "success", label: "Success" },
  { value: "failed", label: "Failed" },
  { value: "partial", label: "Partial" },
];

export const RUN_TRIGGER_OPTIONS: { value: RunTrigger; label: string }[] = [
  { value: "manual", label: "Manual" },
  { value: "scheduled", label: "Scheduled" },
];

const RUN_STATUSES = new Set<JobRunStatus>(RUN_STATUS_OPTIONS.map((option) => option.value));
const RUN_TRIGGERS = new Set<RunTrigger>(RUN_TRIGGER_OPTIONS.map((option) => option.value));

export function parseRunStatus(value: string | null): JobRunStatus | undefined {
  if (value && RUN_STATUSES.has(value as JobRunStatus)) {
    return value as JobRunStatus;
  }
  return undefined;
}

export function parseRunTrigger(value: string | null): RunTrigger | undefined {
  if (value && RUN_TRIGGERS.has(value as RunTrigger)) {
    return value as RunTrigger;
  }
  return undefined;
}

export function filterRuns(
  items: RunListItem[],
  filters: { status?: JobRunStatus; trigger?: RunTrigger },
): RunListItem[] {
  return items.filter((run) => {
    if (filters.status && run.status !== filters.status) {
      return false;
    }
    if (filters.trigger && run.trigger !== filters.trigger) {
      return false;
    }
    return true;
  });
}
