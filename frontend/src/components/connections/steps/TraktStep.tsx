import { Alert, Button, Group, Stack, Text } from "@mantine/core"
import { useMutation } from "@tanstack/react-query"
import { useEffect, useRef, useState } from "react"

import { ApiError } from "src/api/client"
import type { ConnectionSummary, TraktDevicePollInput, TraktDeviceStart } from "src/api/connections"
import { pollTraktDevice, startTraktDevice, testTraktConnection } from "src/api/connectionsApi"
import { isConnectionConfigured } from "src/components/connections/connectionFormHelpers"
import { TestConnectionButton } from "src/components/connections/connectionTestFeedback"
import { ClearConnectionButton } from "src/components/connections/steps/ClearConnectionButton"
import { useConnectionTestFeedback } from "src/components/connections/useConnectionTestFeedback"
import { ConnectIcon } from "src/components/icons/ConnectIcon"
import { showToast } from "src/toast"

export function TraktStep({
  connection,
  onSaved,
  onCleared,
}: {
  connection: ConnectionSummary | undefined
  onSaved: () => void
  onCleared: () => void
}) {
  const [device, setDevice] = useState<TraktDeviceStart | null>(null)

  const start = useMutation({
    mutationFn: startTraktDevice,
    onSuccess: (data) => {
      setDevice(data)
      showToast({ color: "blue", message: "Visit Trakt to authorize this device" })
    },
    onError: (error: unknown) => {
      showToast({
        color: "red",
        message: error instanceof ApiError ? String(error.message) : "Trakt authorization failed",
      })
    },
  })

  const poll = useMutation({
    mutationFn: (body: TraktDevicePollInput) => pollTraktDevice(body),
    onSuccess: (data) => {
      if (data.status === "ok") {
        setDevice(null)
        showToast({ color: "green", message: "Trakt connected" })
        onSaved()
      }
    },
    onError: (error: unknown) => {
      showToast({
        color: "red",
        message: error instanceof ApiError ? String(error.message) : "Trakt authorization failed",
      })
    },
  })
  const pollMutate = useRef(poll.mutate)
  pollMutate.current = poll.mutate

  useEffect(() => {
    if (!device || poll.isPending) return undefined
    const timer = window.setInterval(
      () => {
        pollMutate.current({ device_code: device.device_code })
      },
      (device.interval || 5) * 1000,
    )
    return () => window.clearInterval(timer)
  }, [device, poll.isPending])

  const configured = isConnectionConfigured(connection)
  const traktConnected = connection?.status === "ok"
  const { testStatus, onTestSuccess, onTestError, resetTestStatus } = useConnectionTestFeedback()

  useEffect(() => {
    resetTestStatus()
  }, [connection?.service, connection?.status, resetTestStatus])

  const testSaved = useMutation({
    mutationFn: testTraktConnection,
    onSuccess: onTestSuccess,
    onError: (error: unknown) => onTestError(error, "Trakt test failed"),
  })

  return (
    <Stack gap="sm">
      <Text c="dimmed" size="sm">
        Authorize plextraktbox to access your Trakt account. You will visit Trakt and enter a one-time code.
      </Text>
      {traktConnected ? (
        <Alert color="green" title="Trakt connected">
          <Text size="sm">Your Trakt account is authorized for sync.</Text>
        </Alert>
      ) : null}
      <Group wrap="wrap">
        {configured ? (
          <TestConnectionButton testStatus={testStatus} onClick={() => testSaved.mutate()} loading={testSaved.isPending} />
        ) : null}
        <Button
          onClick={() => start.mutate()}
          loading={start.isPending}
          disabled={traktConnected || device !== null}
          leftSection={<ConnectIcon />}
        >
          Connect Trakt
        </Button>
        {configured ? <ClearConnectionButton service="trakt" connection={connection} onCleared={onCleared} /> : null}
      </Group>
      {device ? (
        <Alert color="blue" title="Authorize on Trakt">
          <Stack gap="xs">
            <Text size="sm">
              Visit{" "}
              <a href={device.verification_url} target="_blank" rel="noreferrer">
                {device.verification_url}
              </a>{" "}
              and enter code <strong>{device.user_code}</strong>.
            </Text>
            <Text size="sm" c="dimmed">
              Waiting for authorization…
            </Text>
          </Stack>
        </Alert>
      ) : null}
    </Stack>
  )
}
