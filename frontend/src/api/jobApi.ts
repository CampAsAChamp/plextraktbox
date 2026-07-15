import { api } from "./client";
import type { Job, JobInput, JobRun, SchedulePreview } from "./jobs";

export function listJobs() {
  return api.get<Job[]>("/jobs");
}

export function getJob(id: number) {
  return api.get<Job>(`/jobs/${id}`);
}

export function createJob(input: JobInput) {
  return api.post<Job>("/jobs", input);
}

export function updateJob(id: number, input: JobInput) {
  return api.put<Job>(`/jobs/${id}`, input);
}

export function deleteJob(id: number) {
  return api.del<void>(`/jobs/${id}`);
}

export function runJob(id: number, dryRun?: boolean) {
  return api.post<JobRun>(`/jobs/${id}/run`, dryRun === undefined ? undefined : { dry_run: dryRun });
}

export function previewSchedule(cron: string, count = 5) {
  return api.post<SchedulePreview>("/jobs/schedule-preview", { cron, count });
}
