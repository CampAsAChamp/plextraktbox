import { Anchor, Avatar, Group, Paper, SegmentedControl, Stack, Text, Title } from "@mantine/core";
import type { User } from "../api/auth";
import { useDisplayPreferences } from "../settings/DisplayPreferencesProvider";
import { TimezonePreferenceControls } from "../settings/TimezonePreferenceControls";
import { NotificationSettings } from "../components/notifications/NotificationSettings";
import { formatDateTime } from "../utils/dateTimeFormat";

const TIME_FORMAT_OPTIONS = [
  { value: "24h", label: "24-hour" },
  { value: "12h", label: "12-hour (AM/PM)" },
] as const;

const DATE_FORMAT_OPTIONS = [
  { value: "mdy", label: "MM/DD/YYYY" },
  { value: "dmy", label: "DD/MM/YYYY" },
] as const;

const PREVIEW_TIMESTAMP = "2026-07-11T18:30:45.123Z";

interface SettingsPageProps {
  user: User;
}

export function SettingsPage({ user }: SettingsPageProps) {
  const { preferences, setTimeFormat, setDateFormat } = useDisplayPreferences();

  return (
    <Stack gap="md" maw="85%" mx="auto">
      <Title order={3}>Settings</Title>

      <Paper withBorder p="md" radius="md">
        <Stack gap="md">
          <Text fw={500}>Account</Text>
          <Group gap="md" align="flex-start" wrap="nowrap">
            <Avatar src={user.avatar_url} alt="" size={64} radius="xl" />
            <Stack gap={4}>
              <Text fw={600}>{user.username}</Text>
              <Text size="sm" c="dimmed">
                {user.email}
              </Text>
              <Anchor
                href="https://gravatar.com"
                target="_blank"
                rel="noopener noreferrer"
                size="sm"
              >
                Manage avatar at Gravatar
              </Anchor>
            </Stack>
          </Group>
        </Stack>
      </Paper>

      <Paper withBorder p="md" radius="md">
        <Stack gap="lg">
          <TimezonePreferenceControls />

          <Stack gap="xs">
            <Text fw={500}>Date format</Text>
            <Text size="sm" c="dimmed">
              Choose month-first (US) or day-first date ordering.
            </Text>
            <SegmentedControl
              value={preferences.dateFormat}
              onChange={(value) => setDateFormat(value as typeof preferences.dateFormat)}
              data={[...DATE_FORMAT_OPTIONS]}
            />
          </Stack>

          <Stack gap="xs">
            <Text fw={500}>Time format</Text>
            <Text size="sm" c="dimmed">
              Choose between 24-hour time and 12-hour time with AM/PM.
            </Text>
            <SegmentedControl
              value={preferences.timeFormat}
              onChange={(value) => setTimeFormat(value as typeof preferences.timeFormat)}
              data={[...TIME_FORMAT_OPTIONS]}
            />
          </Stack>

          <Stack gap={4}>
            <Text size="sm" fw={500}>
              Preview
            </Text>
            <Text size="sm" c="dimmed">
              {formatDateTime(PREVIEW_TIMESTAMP, preferences)}
            </Text>
          </Stack>
        </Stack>
      </Paper>

      <NotificationSettings />
    </Stack>
  );
}
