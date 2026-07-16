/** Common schedule presets (APScheduler weekday 0 = Monday). */

export interface CronPreset {
  id: string
  label: string
  cron: string
  /** Base description; append cron timezone in the UI. */
  description: string
}

export const CRON_PRESETS: CronPreset[] = [
  {
    id: "daily-3am",
    label: "Daily 3am",
    cron: "0 3 * * *",
    description: "Every day at 03:00",
  },
  {
    id: "every-6h",
    label: "Every 6 hours",
    cron: "0 */6 * * *",
    description: "Every 6 hours on the hour",
  },
  {
    id: "weekly",
    label: "Weekly",
    cron: "0 3 * * 0",
    description: "Every Monday at 03:00",
  },
]

export function matchCronPreset(cron: string): string | null {
  const trimmed = cron.trim()
  const preset = CRON_PRESETS.find((item) => item.cron === trimmed)
  return preset?.id ?? null
}
