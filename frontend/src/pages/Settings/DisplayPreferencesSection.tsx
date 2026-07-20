import { Code, Paper, SegmentedControl, Stack, Text } from "@mantine/core"

import { ClockIcon } from "src/components/icons/ClockIcon"
import { SettingsSectionTitle } from "src/components/SettingsSectionTitle"
import { useDisplayPreferences } from "src/settings/DisplayPreferencesProvider"
import { TimezonePreferenceControls } from "src/settings/TimezonePreferenceControls"
import { formatDateTime } from "src/utils/dateTimeFormat"

const TIME_FORMAT_OPTIONS = [
  { value: "24h", label: "24-hour" },
  { value: "12h", label: "12-hour (AM/PM)" },
] as const

const YEAR_FORMAT_OPTIONS = [
  { value: "2-digit", label: "YY" },
  { value: "numeric", label: "YYYY" },
] as const

/** Afternoon in US zones so 24h vs 12h (e.g. 15:30 vs 3:30 PM) is obvious. */
const PREVIEW_TIMESTAMP = "2026-07-11T22:30:45.123Z"

export function DisplayPreferencesSection() {
  const { preferences, setTimeFormat, setDateFormat, setYearFormat } = useDisplayPreferences()
  const yearToken = preferences.yearFormat === "2-digit" ? "YY" : "YYYY"
  const dateFormatOptions = [
    { value: "mdy", label: `MM/DD/${yearToken}` },
    { value: "dmy", label: `DD/MM/${yearToken}` },
  ]

  return (
    <Paper id="settings-display" withBorder p="md" data-settings-section="Display preferences" style={{ scrollMarginTop: 80 }}>
      <Stack gap="lg">
        <SettingsSectionTitle icon={<ClockIcon size={18} />}>Display preferences</SettingsSectionTitle>
        <TimezonePreferenceControls />

        <Stack gap="xs">
          <Text fw={500}>Date format</Text>
          <Text size="sm" c="dimmed">
            Choose month-first (US) or day-first date ordering.
          </Text>
          <SegmentedControl
            fullWidth
            value={preferences.dateFormat}
            onChange={(value) => setDateFormat(value as typeof preferences.dateFormat)}
            data={dateFormatOptions}
          />
        </Stack>

        <Stack gap="xs">
          <Text fw={500}>Year format</Text>
          <Text size="sm" c="dimmed">
            Show years as two digits (26) or four digits (2026).
          </Text>
          <SegmentedControl
            fullWidth
            value={preferences.yearFormat}
            onChange={(value) => setYearFormat(value as typeof preferences.yearFormat)}
            data={[...YEAR_FORMAT_OPTIONS]}
          />
        </Stack>

        <Stack gap="xs">
          <Text fw={500}>Time format</Text>
          <Text size="sm" c="dimmed">
            Choose between 24-hour time and 12-hour time with AM/PM.
          </Text>
          <SegmentedControl
            fullWidth
            value={preferences.timeFormat}
            onChange={(value) => setTimeFormat(value as typeof preferences.timeFormat)}
            data={[...TIME_FORMAT_OPTIONS]}
          />
        </Stack>

        <Stack gap={6}>
          <Text size="sm" fw={500}>
            Preview
          </Text>
          <Code
            block
            style={{
              fontSize: "var(--mantine-font-size-md)",
              fontWeight: 600,
              width: "fit-content",
            }}
          >
            {formatDateTime(PREVIEW_TIMESTAMP, preferences)}
          </Code>
        </Stack>
      </Stack>
    </Paper>
  )
}
