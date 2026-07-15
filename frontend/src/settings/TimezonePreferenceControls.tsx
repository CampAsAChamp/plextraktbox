import { Group, SegmentedControl, Select, Stack, Text } from "@mantine/core";
import type { ReactNode } from "react";
import { useMemo } from "react";
import { ClockIcon } from "../components/icons/ClockIcon";
import { GlobeIcon } from "../components/icons/GlobeIcon";
import { MapPinIcon } from "../components/icons/MapPinIcon";
import { useDisplayPreferences } from "./DisplayPreferencesProvider";
import {
  formatTimezoneLabel,
  getBrowserTimezone,
  getManualTimezone,
  getTimezoneMode,
  listIanaTimezones,
} from "./displayPreferences";

function modeLabel(icon: ReactNode, text: string, title: string) {
  return (
    <Group gap={6} wrap="nowrap" justify="center" title={title}>
      {icon}
      <span>{text}</span>
    </Group>
  );
}

/** Shared Local → UTC → Manual order for display prefs and cron timezone. */
export const TIMEZONE_MODE_OPTIONS = [
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

type TimezonePreferenceControlsProps = {
  compact?: boolean;
};

export function TimezonePreferenceControls({ compact = false }: TimezonePreferenceControlsProps) {
  const { preferences, setTimezone } = useDisplayPreferences();
  const timezoneMode = getTimezoneMode(preferences.timezone);
  const manualTimezone = getManualTimezone(preferences.timezone);
  const browserTimezone = getBrowserTimezone();

  const timezoneOptions = useMemo(
    () =>
      listIanaTimezones().map((timezone) => ({
        value: timezone,
        label: formatTimezoneLabel(timezone),
      })),
    [],
  );

  const handleModeChange = (value: string) => {
    if (value === "local") {
      setTimezone("local");
      return;
    }
    if (value === "utc") {
      setTimezone("utc");
      return;
    }
    setTimezone(manualTimezone);
  };

  const manualTimezoneSelect = (
    <Select
      searchable
      label={compact ? undefined : "Manual timezone"}
      placeholder="Select a timezone"
      nothingFoundMessage="No timezones found"
      data={timezoneOptions}
      value={manualTimezone}
      onChange={(value) => value && setTimezone(value)}
      w={compact ? { base: "100%", sm: 220 } : undefined}
      styles={TIMEZONE_SELECT_STYLES}
    />
  );

  if (compact) {
    return (
      <Stack gap={4} style={{ flex: "1 1 200px", minWidth: 0 }}>
        <Text component="label" size="sm" fw={500}>
          Timezone
        </Text>
        <Group align="flex-end" gap="xs" wrap="wrap">
          <SegmentedControl
            value={timezoneMode}
            onChange={handleModeChange}
            data={[...TIMEZONE_MODE_OPTIONS]}
            style={{ flex: "1 1 auto", minWidth: 0 }}
          />
          {timezoneMode === "manual" ? manualTimezoneSelect : null}
        </Group>
      </Stack>
    );
  }

  return (
    <Stack gap="xs">
      <Text fw={500}>Timezone</Text>
      <Text size="sm" c="dimmed">
        Use your browser timezone, UTC, or pick a specific IANA timezone for displaying
        timestamps. Job cron schedules use the separate Cron timezone under Sync defaults.
      </Text>
      <SegmentedControl
        fullWidth
        value={timezoneMode}
        onChange={handleModeChange}
        data={[...TIMEZONE_MODE_OPTIONS]}
      />
      {timezoneMode === "local" ? (
        <Text size="sm" c="dimmed">
          <Text span fw={600} inherit>
            Browser Timezone:
          </Text>{" "}
          {formatTimezoneLabel(browserTimezone)}
        </Text>
      ) : null}
      {timezoneMode === "manual" ? manualTimezoneSelect : null}
    </Stack>
  );
}
