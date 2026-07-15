import { Group, Stack, Title } from "@mantine/core";
import type { User } from "../../api/auth";
import { NotificationSettings } from "../../components/notifications/NotificationSettings";
import { AccountSection } from "./AccountSection";
import { DisplayPreferencesSection } from "./DisplayPreferencesSection";
import { BackupSection } from "./BackupSection";
import { SettingsMobileNav, SettingsToc } from "./SettingsToc";
import { SyncSettingsSection } from "./SyncSettingsSection";
import { ThemeSection } from "./ThemeSection";

interface SettingsPageProps {
  user: User;
}

export function SettingsPage({ user }: SettingsPageProps) {
  return (
    <Stack gap="md" maw={1100} mx="auto">
      <Title order={3}>Settings</Title>
      <SettingsMobileNav />
      <Group align="flex-start" gap="xl" wrap="nowrap">
        <SettingsToc />
        <Stack gap="md" style={{ flex: 1, minWidth: 0 }}>
          <AccountSection user={user} />
          <SyncSettingsSection />
          <BackupSection />
          <DisplayPreferencesSection />
          <ThemeSection />
          <NotificationSettings />
        </Stack>
      </Group>
    </Stack>
  );
}
