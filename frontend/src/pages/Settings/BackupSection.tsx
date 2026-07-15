import { Button, Paper, Stack, Text } from "@mantine/core";
import { showToast } from "../../toast";
import { useState } from "react";
import { downloadBackup } from "../../api/settings";
import { SettingsSectionTitle } from "../../components/SettingsSectionTitle";
import { DatabaseIcon } from "../../components/icons/DatabaseIcon";
import { DownloadIcon } from "../../components/icons/DownloadIcon";

export function BackupSection() {
  const [loading, setLoading] = useState(false);

  async function handleBackup() {
    setLoading(true);
    try {
      await downloadBackup();
      showToast({ color: "green", message: "Database backup downloaded" });
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : "Backup failed";
      showToast({ color: "red", message });
    } finally {
      setLoading(false);
    }
  }

  return (
    <Paper
      id="settings-backup"
      withBorder
      p="md"
      data-settings-section="Backup"
      style={{ scrollMarginTop: 80 }}
    >
      <Stack gap="md">
        <SettingsSectionTitle icon={<DatabaseIcon size={18} />}>Backup</SettingsSectionTitle>
        <Text size="sm" c="dimmed">
          Download a consistent SQLite snapshot. On TrueNAS, prefer ZFS snapshots of the{" "}
          <code>/data</code> dataset for routine backups.
        </Text>
        <Button
          variant="light"
          loading={loading}
          onClick={() => void handleBackup()}
          leftSection={<DownloadIcon />}
          maw={280}
        >
          Download database backup
        </Button>
      </Stack>
    </Paper>
  );
}
