import { Alert, Button, Checkbox, Group, Stack, Text } from "@mantine/core"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useEffect, useRef, useState } from "react"

import { ApiError } from "src/api/client"
import type { ConnectionSummary, PlexPinPollInput, PlexPinStart } from "src/api/connections"
import { getPlexLibraries, pollPlexPin, startPlexPin, testPlexConnection, updatePlexLibraries } from "src/api/connectionsApi"
import { isConnectionConfigured } from "src/components/connections/connectionFormHelpers"
import { TestConnectionButton } from "src/components/connections/connectionTestFeedback"
import { ClearConnectionButton } from "src/components/connections/steps/ClearConnectionButton"
import { useConnectionTestFeedback } from "src/components/connections/useConnectionTestFeedback"
import { ConnectIcon } from "src/components/icons/ConnectIcon"
import { FilmIcon } from "src/components/icons/FilmIcon"
import { SaveIcon } from "src/components/icons/SaveIcon"
import { TvIcon } from "src/components/icons/TvIcon"
import { showToast } from "src/toast"

function PlexLibraryPicker({ enabled }: { enabled: boolean }) {
  const queryClient = useQueryClient()
  const librariesQuery = useQuery({
    queryKey: ["connections", "plex", "libraries"],
    queryFn: getPlexLibraries,
    enabled,
  })
  const [selected, setSelected] = useState<string[]>([])

  useEffect(() => {
    if (librariesQuery.data) {
      setSelected(librariesQuery.data.selected_ids)
    }
  }, [librariesQuery.data])

  const save = useMutation({
    mutationFn: updatePlexLibraries,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["connections"] })
      queryClient.invalidateQueries({ queryKey: ["connections", "plex", "libraries"] })
      showToast({ color: "green", message: "Plex library selection saved" })
    },
    onError: (error: unknown) => {
      showToast({
        color: "red",
        message: error instanceof ApiError ? String(error.message) : "Could not save Plex libraries",
      })
    },
  })

  if (!enabled) {
    return null
  }

  if (librariesQuery.isLoading) {
    return <Text size="sm">Loading Plex libraries…</Text>
  }

  if (librariesQuery.isError || !librariesQuery.data) {
    return (
      <Alert color="yellow" title="Could not load Plex libraries">
        Connect and test Plex first, then choose which Plex libraries to sync.
      </Alert>
    )
  }

  const { libraries } = librariesQuery.data
  if (libraries.length === 0) {
    return (
      <Alert color="yellow" title="No Plex libraries">
        Add a movie or show library to your Plex server to sync ratings and watched history.
      </Alert>
    )
  }

  return (
    <Stack gap="xs">
      <Text fw={500} size="sm">
        Plex libraries to sync
      </Text>
      <Text c="dimmed" size="sm">
        Movie ratings and movie/episode watched history are fetched from the libraries you select. Show libraries enable episode watched
        sync; leave all unchecked to include every movie and show library.
      </Text>
      <Checkbox.Group value={selected} onChange={setSelected}>
        <Stack gap="xs">
          {libraries.map((library) => (
            <Checkbox
              key={library.id}
              value={library.id}
              label={
                <Group gap="xs" wrap="nowrap">
                  {library.type === "show" ? <TvIcon /> : <FilmIcon />}
                  <span>{library.title}</span>
                  <Text size="sm" c="dimmed" component="span">
                    {library.type === "show" ? "TV" : "Movies"}
                  </Text>
                </Group>
              }
            />
          ))}
        </Stack>
      </Checkbox.Group>
      <Button variant="light" w="fit-content" loading={save.isPending} leftSection={<SaveIcon />} onClick={() => save.mutate(selected)}>
        Save Plex library selection
      </Button>
    </Stack>
  )
}

export function PlexStep({
  connection,
  onSaved,
  onCleared,
}: {
  connection: ConnectionSummary | undefined
  onSaved: () => void
  onCleared: () => void
}) {
  const [pin, setPin] = useState<PlexPinStart | null>(null)
  const [polling, setPolling] = useState(false)
  const [pollError, setPollError] = useState<string | null>(null)
  const pinRef = useRef<PlexPinStart | null>(null)
  pinRef.current = pin

  const start = useMutation({
    mutationFn: startPlexPin,
    onSuccess: (data) => {
      setPollError(null)
      setPin(data)
      setPolling(true)
      showToast({ color: "blue", message: "Sign in to Plex to authorize plextraktbox" })
    },
    onError: (error: unknown) => {
      showToast({
        color: "red",
        message: error instanceof ApiError ? String(error.message) : "Plex authorization failed",
      })
    },
  })

  const poll = useMutation({
    mutationFn: (body: PlexPinPollInput) => pollPlexPin(body),
    onSuccess: (data) => {
      if (data.status === "ok") {
        setPolling(false)
        setPin(null)
        showToast({ color: "green", message: "Plex connected" })
        onSaved()
      }
    },
    onError: (error: unknown) => {
      setPolling(false)
      const message = error instanceof ApiError ? String(error.message) : "Plex authorization failed"
      setPollError(message)
      showToast({ color: "red", message })
    },
  })
  const pollMutate = useRef(poll.mutate)
  pollMutate.current = poll.mutate

  useEffect(() => {
    if (!polling || !pinRef.current || poll.isPending) return undefined
    const timer = window.setInterval(
      () => {
        const activePin = pinRef.current
        if (!activePin?.pin_code) return
        pollMutate.current({ pin_id: activePin.pin_id, pin_code: activePin.pin_code })
      },
      (pinRef.current.interval || 2) * 1000,
    )
    return () => window.clearInterval(timer)
  }, [polling, pin, poll.isPending])

  useEffect(() => () => setPolling(false), [])

  function cancelAuthorization() {
    setPolling(false)
    setPollError(null)
    setPin(null)
  }

  const showManualCode = pin ? pin.pin_code.length <= 8 : false
  const configured = isConnectionConfigured(connection)
  const plexConnected = connection?.status === "ok"
  const { testStatus, onTestSuccess, onTestError, resetTestStatus } = useConnectionTestFeedback()

  useEffect(() => {
    resetTestStatus()
  }, [connection?.service, connection?.status, resetTestStatus])

  const testSaved = useMutation({
    mutationFn: testPlexConnection,
    onSuccess: onTestSuccess,
    onError: (error: unknown) => onTestError(error, "Plex test failed"),
  })

  return (
    <Stack gap="sm">
      <Text c="dimmed" size="sm">
        Authorize plextraktbox to access your Plex account. Your server will be discovered automatically after you sign in.
      </Text>
      {plexConnected && connection ? (
        <Alert color="green" title="Plex connected">
          <Text size="sm">
            {typeof connection.config.friendly_name === "string" ? connection.config.friendly_name : "Plex server"}
            {typeof connection.config.url === "string" ? ` — ${connection.config.url}` : ""}
          </Text>
        </Alert>
      ) : null}
      <Group wrap="wrap">
        <Button
          onClick={() => start.mutate()}
          loading={start.isPending}
          disabled={plexConnected || pin !== null}
          leftSection={<ConnectIcon />}
        >
          Connect Plex
        </Button>
        {configured ? (
          <TestConnectionButton testStatus={testStatus} onClick={() => testSaved.mutate()} loading={testSaved.isPending} />
        ) : null}
        <ClearConnectionButton service="plex" connection={connection} onCleared={onCleared} />
      </Group>
      {pollError ? (
        <Alert color="red" title="Could not finish Plex setup">
          <Stack gap="xs">
            <Text size="sm">{pollError}</Text>
            <Button
              size="xs"
              variant="light"
              onClick={() => {
                cancelAuthorization()
                start.mutate()
              }}
            >
              Try again
            </Button>
          </Stack>
        </Alert>
      ) : null}
      {pin ? (
        <Alert color="blue" title="Authorize on Plex">
          <Stack gap="xs">
            <Text size="sm">
              Sign in to Plex and approve access for plextraktbox. Use the same browser session where you are already signed in to Plex, or
              sign in when prompted.
            </Text>
            <Button component="a" href={pin.auth_url} target="_blank" rel="noreferrer" variant="light">
              Open Plex authorization
            </Button>
            {showManualCode ? (
              <Text size="sm">
                Or visit{" "}
                <a href={pin.verification_url} target="_blank" rel="noreferrer">
                  {pin.verification_url}
                </a>{" "}
                and enter code <strong>{pin.pin_code}</strong>.
              </Text>
            ) : null}
            <Text size="sm" c="dimmed">
              Waiting for authorization…
            </Text>
            <Button variant="subtle" size="xs" onClick={cancelAuthorization}>
              Cancel
            </Button>
          </Stack>
        </Alert>
      ) : null}
      <PlexLibraryPicker enabled={plexConnected} />
    </Stack>
  )
}
