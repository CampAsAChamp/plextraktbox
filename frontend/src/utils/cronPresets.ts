/** Common schedule presets (APScheduler weekday 0 = Monday). */

export interface CronPreset {
  id: string;
  label: string;
  cron: string;
  /** Base description; append cron timezone in the UI. */
  description: string;
}

export const CRON_PRESETS: CronPreset[] = [
  {
    id: "daily",
    label: "Daily",
    cron: "0 3 * * *",
    description: "Every day at 03:00",
  },
  {
    id: "weekly",
    label: "Weekly",
    cron: "0 3 * * 0",
    description: "Every Monday at 03:00",
  },
];

export function matchCronPreset(cron: string): string | null {
  const trimmed = cron.trim();
  const preset = CRON_PRESETS.find((item) => item.cron === trimmed);
  return preset?.id ?? null;
}
