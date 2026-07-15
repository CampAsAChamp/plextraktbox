import { Group, Stack, Title } from "@mantine/core";
import type { User } from "../../api/auth";
import { NotificationSettings } from "../../components/notifications/NotificationSettings";
import { AccountSection } from "./AccountSection";
import { DisplayPreferencesSection } from "./DisplayPreferencesSection";
import { BackupSection } from "./BackupSection";
import { SettingsToc } from "./SettingsToc";
import { SyncSettingsSection } from "./SyncSettingsSection";

interface SettingsPageProps {
  user: User;
}

export function SettingsPage({ user }: SettingsPageProps) {
  return (
    <Stack gap="md" maw={1100} mx="auto">
      <Title order={3}>Settings</Title>
      <Group align="flex-start" gap="xl" wrap="nowrap">
        <SettingsToc />
        <Stack gap="md" style={{ flex: 1, minWidth: 0 }}>
          <AccountSection user={user} />
          <SyncSettingsSection />
          <BackupSection />
          <DisplayPreferencesSection />
          <NotificationSettings />
        </Stack>
      </Group>
    </Stack>
  );
}
