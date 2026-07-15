/** Common schedule presets (UTC cron; APScheduler weekday 0 = Monday). */

export interface CronPreset {
  id: string;
  label: string;
  cron: string;
  description: string;
}

export const CRON_PRESETS: CronPreset[] = [
  {
    id: "daily",
    label: "Daily",
    cron: "0 3 * * *",
    description: "Every day at 03:00 UTC",
  },
  {
    id: "weekly",
    label: "Weekly",
    cron: "0 3 * * 0",
    description: "Every Monday at 03:00 UTC",
  },
];

export function matchCronPreset(cron: string): string | null {
  const trimmed = cron.trim();
  const preset = CRON_PRESETS.find((item) => item.cron === trimmed);
  return preset?.id ?? null;
}
