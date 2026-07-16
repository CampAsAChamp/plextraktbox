import { Button, FileButton, Group, Modal, Paper, Stack, Text } from "@mantine/core"
import { useState } from "react"

import { downloadBackup, restoreBackup } from "src/api/settings"
import { DatabaseIcon } from "src/components/icons/DatabaseIcon"
import { DownloadIcon } from "src/components/icons/DownloadIcon"
import { UploadIcon } from "src/components/icons/UploadIcon"
import { SettingsSectionTitle } from "src/components/SettingsSectionTitle"
import { showToast } from "src/toast"

export function BackupSection() {
  const [downloadLoading, setDownloadLoading] = useState(false)
  const [restoreLoading, setRestoreLoading] = useState(false)
  const [pendingFile, setPendingFile] = useState<File | null>(null)

  async function handleBackup() {
    setDownloadLoading(true)
    try {
      await downloadBackup()
      showToast({ color: "green", message: "Database backup downloaded" })
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : "Backup failed"
      showToast({ color: "red", message })
    } finally {
      setDownloadLoading(false)
    }
  }

  async function handleRestoreConfirm() {
    if (!pendingFile) return
    const file = pendingFile
    setPendingFile(null)
    setRestoreLoading(true)
    try {
      const result = await restoreBackup(file)
      showToast({
        color: "green",
        message: result.message || "Database restored. Reloading…",
      })
      window.setTimeout(() => {
        window.location.reload()
      }, 800)
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : "Restore failed"
      showToast({ color: "red", message })
    } finally {
      setRestoreLoading(false)
    }
  }

  return (
    <Paper id="settings-backup" withBorder p="md" data-settings-section="Backup" style={{ scrollMarginTop: 80 }}>
      <Stack gap="md">
        <SettingsSectionTitle icon={<DatabaseIcon size={18} />}>Backup</SettingsSectionTitle>
        <Text size="sm" c="dimmed">
          Download a consistent SQLite snapshot, or restore from a previous download. Restoring replaces the live database and reloads the
          app. On TrueNAS, prefer ZFS snapshots of the <code>/data</code> dataset for routine backups.
        </Text>
        <Group gap="sm">
          <Button variant="light" loading={downloadLoading} onClick={() => void handleBackup()} leftSection={<DownloadIcon />}>
            Download database backup
          </Button>
          <FileButton
            onChange={(file) => {
              if (file) setPendingFile(file)
            }}
            accept=".db,.sqlite,.sqlite3,application/x-sqlite3"
            disabled={restoreLoading}
          >
            {(props) => (
              <Button variant="light" color="orange" loading={restoreLoading} leftSection={<UploadIcon />} {...props}>
                Restore from backup
              </Button>
            )}
          </FileButton>
        </Group>
      </Stack>

      <Modal
        opened={pendingFile !== null}
        onClose={() => {
          if (!restoreLoading) setPendingFile(null)
        }}
        title="Restore database"
        centered
      >
        <Stack gap="md">
          <Text size="sm">
            Replace the live database with{" "}
            <Text span fw={600}>
              {pendingFile?.name}
            </Text>
            ? This cannot be undone from the UI. A copy of the current database is kept as <code>plextraktbox.db.pre-restore</code> on disk.
          </Text>
          <Group justify="flex-end" gap="sm">
            <Button variant="default" disabled={restoreLoading} onClick={() => setPendingFile(null)}>
              Cancel
            </Button>
            <Button color="orange" loading={restoreLoading} leftSection={<UploadIcon />} onClick={() => void handleRestoreConfirm()}>
              Restore
            </Button>
          </Group>
        </Stack>
      </Modal>
    </Paper>
  )
}
