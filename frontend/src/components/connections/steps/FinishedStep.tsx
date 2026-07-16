import { Alert, Button, Stack, Text } from "@mantine/core"

import { StatusCheckIcon } from "src/components/connections/StatusCheckIcon"
import { HomeIcon } from "src/components/icons/HomeIcon"

export function FinishedStep({ onGoToDashboard }: { onGoToDashboard: () => void }) {
  return (
    <Stack gap="md">
      <Alert
        color="green"
        title="All connections successful"
        icon={
          <span style={{ display: "inline-flex" }}>
            <StatusCheckIcon size={16} />
          </span>
        }
      >
        <Text size="sm">
          Plex, Trakt, Letterboxd, and TMDB are configured and ready for sync. Use the steps above anytime to review or update a connection.
        </Text>
      </Alert>
      <Button onClick={onGoToDashboard} w="fit-content" leftSection={<HomeIcon />}>
        Go to dashboard
      </Button>
    </Stack>
  )
}
