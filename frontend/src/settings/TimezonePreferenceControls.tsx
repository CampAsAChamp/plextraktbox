import { Group, SegmentedControl, Select, Stack, Text } from "@mantine/core";
import { useMemo } from "react";
import { useDisplayPreferences } from "./DisplayPreferencesProvider";
import {
  formatTimezoneLabel,
  getBrowserTimezone,
  getFixedTimezone,
  getTimezoneMode,
  listIanaTimezones,
} from "./displayPreferences";

const TIMEZONE_MODE_OPTIONS = [
  { value: "local", label: "Local" },
  { value: "utc", label: "UTC" },
  { value: "fixed", label: "Fixed" },
] as const;

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
  const fixedTimezone = getFixedTimezone(preferences.timezone);
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
    setTimezone(fixedTimezone);
  };

  const fixedTimezoneSelect = (
    <Select
      searchable
      label={compact ? undefined : "Fixed timezone"}
      placeholder="Select a timezone"
      nothingFoundMessage="No timezones found"
      data={timezoneOptions}
      value={fixedTimezone}
      onChange={(value) => value && setTimezone(value)}
      w={compact ? 220 : undefined}
      styles={TIMEZONE_SELECT_STYLES}
    />
  );

  if (compact) {
    return (
      <Stack gap={4}>
        <Text component="label" size="sm" fw={500}>
          Timezone
        </Text>
        <Group align="flex-end" gap="xs" wrap="nowrap">
          <SegmentedControl
            value={timezoneMode}
            onChange={handleModeChange}
            data={[...TIMEZONE_MODE_OPTIONS]}
          />
          {timezoneMode === "fixed" ? fixedTimezoneSelect : null}
        </Group>
      </Stack>
    );
  }

  return (
    <Stack gap="xs">
      <Text fw={500}>Timezone</Text>
      <Text size="sm" c="dimmed">
        Use your browser timezone, UTC, or pick a specific IANA timezone. Changes here and in
        the log viewer use the same saved preference.
      </Text>
      <SegmentedControl
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
      {timezoneMode === "fixed" ? fixedTimezoneSelect : null}
    </Stack>
  );
}
