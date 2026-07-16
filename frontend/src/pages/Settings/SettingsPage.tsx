import { Group, Stack, Title } from "@mantine/core";
import type { User } from "src/api/auth";
import { NotificationSettings } from "src/components/notifications/NotificationSettings";
import { AccountSection } from "src/pages/Settings/AccountSection";
import { DisplayPreferencesSection } from "src/pages/Settings/DisplayPreferencesSection";
import { BackupSection } from "src/pages/Settings/BackupSection";
import { SettingsMobileNav, SettingsToc } from "src/pages/Settings/SettingsToc";
import { SyncCachesSection } from "src/pages/Settings/SyncCachesSection";
import { SyncSettingsSection } from "src/pages/Settings/SyncSettingsSection";
import { ThemeSection } from "src/pages/Settings/ThemeSection";

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
          <SyncCachesSection />
          <BackupSection />
          <DisplayPreferencesSection />
          <ThemeSection />
          <NotificationSettings />
        </Stack>
      </Group>
    </Stack>
  );
}
