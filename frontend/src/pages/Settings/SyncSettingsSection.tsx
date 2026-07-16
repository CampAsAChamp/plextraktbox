import {
  Button,
  Group,
  Paper,
  SegmentedControl,
  Select,
  Stack,
  Switch,
  Text,
  Textarea,
  TextInput,
} from "@mantine/core";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useMemo, useState, type FormEvent, type ReactNode } from "react";
import { z } from "zod";
import { ApiError } from "src/api/client";
import {
  formatExcludeLines,
  getSettings,
  parseExcludeLines,
  updateSettings,
  type AppSettingsInput,
} from "src/api/settings";
import { SettingsSectionTitle } from "src/components/SettingsSectionTitle";
import { ClockIcon } from "src/components/icons/ClockIcon";
import { GlobeIcon } from "src/components/icons/GlobeIcon";
import { MapPinIcon } from "src/components/icons/MapPinIcon";
import { SaveIcon } from "src/components/icons/SaveIcon";
import { SyncIcon } from "src/components/icons/SyncIcon";
import {
  formatTimezoneLabel,
  getBrowserTimezone,
  getManualTimezone,
  getTimezoneMode,
  isValidIanaTimezone,
  listIanaTimezones,
  type TimezoneMode,
  type TimezonePreference,
} from "src/settings/displayPreferences";
import { showToast } from "src/toast";
import { CRON_INVALID_MESSAGE, isValidCronExpression } from "src/utils/cron";

const syncSchema = z.object({
  default_cron: z
    .string()
    .min(1, "Cron expression is required")
    .refine(isValidCronExpression, { message: CRON_INVALID_MESSAGE }),
  cron_timezone: z
    .string()
    .min(1)
    .refine(
      (value) => value === "UTC" || value === "local" || isValidIanaTimezone(value),
      { message: "Choose a valid timezone" },
    ),
  global_dry_run: z.boolean(),
});

function modeLabel(icon: ReactNode, text: string, title: string) {
  return (
    <Group gap={6} wrap="nowrap" justify="center" title={title}>
      {icon}
      <span>{text}</span>
    </Group>
  );
}

const CRON_TIMEZONE_MODE_OPTIONS = [
  {
    value: "local",
    label: modeLabel(<MapPinIcon size={14} />, "Local", "Uses your device timezone"),
  },
  {
    value: "utc",
    label: modeLabel(<GlobeIcon size={14} />, "UTC", "Coordinated Universal Time"),
  },
  {
    value: "manual",
    label: modeLabel(<ClockIcon size={14} />, "Manual", "Pick a specific timezone"),
  },
];

const TIMEZONE_SELECT_STYLES = {
  input: { cursor: "pointer" },
  section: { cursor: "pointer" },
};

/** Map stored cron preference onto the shared display timezone mode helpers. */
function asTimezonePreference(cronTimezone: string): TimezonePreference {
  if (cronTimezone === "UTC") return "utc";
  return cronTimezone;
}

export function SyncSettingsSection() {
  const queryClient = useQueryClient();
  const settingsQuery = useQuery({
    queryKey: ["settings"],
    queryFn: getSettings,
  });

  const [defaultCron, setDefaultCron] = useState("0 3 * * *");
  const [cronTimezone, setCronTimezone] = useState("UTC");
  const [globalDryRun, setGlobalDryRun] = useState(true);
  const [tmdb, setTmdb] = useState("");
  const [imdb, setImdb] = useState("");
  const [tvdb, setTvdb] = useState("");
  const [retentionDays, setRetentionDays] = useState(30);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const timezoneMode: TimezoneMode = getTimezoneMode(asTimezonePreference(cronTimezone));
  const manualTimezone = getManualTimezone(asTimezonePreference(cronTimezone));
  const browserTimezone = getBrowserTimezone();

  const timezoneOptions = useMemo(
    () =>
      listIanaTimezones().map((timezone) => ({
        value: timezone,
        label: formatTimezoneLabel(timezone),
      })),
    [],
  );

  useEffect(() => {
    const data = settingsQuery.data;
    if (!data) return;
    setDefaultCron(data.default_cron);
    setCronTimezone(data.cron_timezone);
    setGlobalDryRun(data.global_dry_run);
    setTmdb(formatExcludeLines(data.exclude_ids.tmdb));
    setImdb(formatExcludeLines(data.exclude_ids.imdb));
    setTvdb(formatExcludeLines(data.exclude_ids.tvdb));
    setRetentionDays(data.log_retention_days);
  }, [settingsQuery.data]);

  const saveMutation = useMutation({
    mutationFn: (input: AppSettingsInput) => updateSettings(input),
    onSuccess: (data) => {
      void queryClient.setQueryData(["settings"], data);
      void queryClient.invalidateQueries({ queryKey: ["schedule-preview"] });
      void queryClient.invalidateQueries({ queryKey: ["jobs"] });
      showToast({ color: "green", message: "Sync settings saved" });
    },
    onError: (error: unknown) => {
      const message = error instanceof ApiError ? String(error.message) : "Save failed";
      showToast({ color: "red", message });
    },
  });

  function handleTimezoneModeChange(value: string) {
    if (value === "local") {
      setCronTimezone("local");
      return;
    }
    if (value === "utc") {
      setCronTimezone("UTC");
      return;
    }
    setCronTimezone(manualTimezone);
  }

  function cronTimezoneLabel(preference: string): string {
    if (preference === "UTC") return "UTC";
    if (preference === "local") {
      const resolved = settingsQuery.data?.cron_timezone_resolved ?? browserTimezone;
      return formatTimezoneLabel(resolved);
    }
    return formatTimezoneLabel(preference);
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const parsed = syncSchema.safeParse({
      default_cron: defaultCron,
      cron_timezone: cronTimezone,
      global_dry_run: globalDryRun,
    });
    if (!parsed.success) {
      const fieldErrors: Record<string, string> = {};
      for (const issue of parsed.error.issues) {
        fieldErrors[String(issue.path[0] ?? "form")] = issue.message;
      }
      setErrors(fieldErrors);
      return;
    }
    if (retentionDays < 1) {
      setErrors({ log_retention_days: "Must be at least 1 day" });
      return;
    }
    setErrors({});
    const input: AppSettingsInput = {
      default_cron: defaultCron.trim(),
      cron_timezone: cronTimezone,
      log_retention_days: retentionDays,
      global_dry_run: globalDryRun,
      exclude_ids: {
        tmdb: parseExcludeLines(tmdb),
        imdb: parseExcludeLines(imdb),
        tvdb: parseExcludeLines(tvdb),
      },
      letterboxd_export_cache_ttl_hours:
        settingsQuery.data?.letterboxd_export_cache_ttl_hours ?? 24,
      trakt_list_cache_ttl_minutes: settingsQuery.data?.trakt_list_cache_ttl_minutes ?? 30,
    };
    if (cronTimezone === "local") {
      input.cron_local_zone = browserTimezone;
    }
    saveMutation.mutate(input);
  }

  return (
    <Paper
      id="settings-sync"
      withBorder
      p="md"
      data-settings-section="Sync defaults & safety"
      style={{ scrollMarginTop: 80 }}
    >
      <form onSubmit={handleSubmit}>
        <Stack gap="md">
          <SettingsSectionTitle icon={<SyncIcon size={18} />}>
            Sync defaults & safety
          </SettingsSectionTitle>
          <Text size="sm" c="dimmed">
            Defaults apply to new jobs. Exclude lists skip matching items during sync
            (global ∪ per-job).
          </Text>

          <Switch
            label="Global dry-run default for new jobs"
            checked={globalDryRun}
            onChange={(event) => setGlobalDryRun(event.currentTarget.checked)}
            disabled={settingsQuery.isLoading}
          />

          <Stack gap="xs">
            <Text fw={500}>Cron timezone</Text>
            <Text size="sm" c="dimmed">
              How job cron hour/minute fields are interpreted. Separate from display
              preferences (how timestamps are shown).
            </Text>
            <SegmentedControl
              fullWidth
              value={timezoneMode}
              onChange={handleTimezoneModeChange}
              data={[...CRON_TIMEZONE_MODE_OPTIONS]}
              disabled={settingsQuery.isLoading}
            />
            {timezoneMode === "local" ? (
              <Text size="sm" c="dimmed">
                <Text span fw={600} inherit>
                  Device timezone:
                </Text>{" "}
                {formatTimezoneLabel(browserTimezone)}
              </Text>
            ) : null}
            {timezoneMode === "manual" ? (
              <Select
                searchable
                label="Manual timezone"
                placeholder="Select a timezone"
                nothingFoundMessage="No timezones found"
                data={timezoneOptions}
                value={manualTimezone}
                onChange={(value) => value && setCronTimezone(value)}
                error={errors.cron_timezone}
                disabled={settingsQuery.isLoading}
                styles={TIMEZONE_SELECT_STYLES}
              />
            ) : null}
          </Stack>

          <TextInput
            label="Default cron"
            description={`Used when creating a new job (${cronTimezoneLabel(cronTimezone)})`}
            value={defaultCron}
            onChange={(event) => setDefaultCron(event.currentTarget.value)}
            error={errors.default_cron}
            disabled={settingsQuery.isLoading}
            styles={{ input: { fontFamily: "var(--mantine-font-family-monospace)" } }}
          />

          <TextInput
            label="Log retention (days)"
            type="number"
            min={1}
            value={String(retentionDays)}
            onChange={(event) => setRetentionDays(Number(event.currentTarget.value) || 0)}
            error={errors.log_retention_days}
            description="Completed runs and their logs older than this are pruned daily"
            disabled={settingsQuery.isLoading}
          />

          <Textarea
            label="Exclude TMDB IDs"
            description="e.g. 550 — one numeric ID per line"
            minRows={2}
            value={tmdb}
            onChange={(event) => setTmdb(event.currentTarget.value)}
            disabled={settingsQuery.isLoading}
          />
          <Textarea
            label="Exclude IMDb IDs"
            description="e.g. tt0111161 — one per line"
            minRows={2}
            value={imdb}
            onChange={(event) => setImdb(event.currentTarget.value)}
            disabled={settingsQuery.isLoading}
          />
          <Textarea
            label="Exclude TVDB IDs"
            description="e.g. 81189 — one numeric ID per line"
            minRows={2}
            value={tvdb}
            onChange={(event) => setTvdb(event.currentTarget.value)}
            disabled={settingsQuery.isLoading}
          />

          <Group>
            <Button
              type="submit"
              loading={saveMutation.isPending}
              leftSection={<SaveIcon />}
              disabled={settingsQuery.isLoading}
            >
              Save sync settings
            </Button>
          </Group>
        </Stack>
      </form>
    </Paper>
  );
}
