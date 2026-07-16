import { Button, Group, Stack, Stepper, Text, Title } from "@mantine/core"
import { useMediaQuery } from "@mantine/hooks"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useEffect, useRef, useState } from "react"
import { useNavigate } from "react-router-dom"

import { ApiError } from "src/api/client"
import type { Service } from "src/api/connections"
import { clearAllConnections, getConnectionsStatus } from "src/api/connectionsApi"
import { ServiceLogo } from "src/components/connections/ServiceLogo"
import { ServiceStepLabel } from "src/components/connections/ServiceStepLabel"
import { allConnectionsOk, resolveActiveStep, SERVICE_ORDER, stepIconClass } from "src/components/connections/steps/connectionsStepHelpers"
import { FinishedStep } from "src/components/connections/steps/FinishedStep"
import { LetterboxdStep } from "src/components/connections/steps/LetterboxdStep"
import { PlexStep } from "src/components/connections/steps/PlexStep"
import { TmdbStep } from "src/components/connections/steps/TmdbStep"
import { TraktStep } from "src/components/connections/steps/TraktStep"
import { TrashIcon } from "src/components/icons/TrashIcon"
import classes from "src/pages/OnboardingStepper.module.css"
import { showToast } from "src/toast"

export function ConnectionsPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const isNarrow = useMediaQuery("(max-width: 47.997em)")
  const statusQuery = useQuery({
    queryKey: ["connections", "status"],
    queryFn: getConnectionsStatus,
  })

  const [active, setActive] = useState(0)
  const prevNeedsConnectionsRef = useRef<boolean | undefined>(undefined)

  const needsConnections = statusQuery.data?.needs_connections === true

  useEffect(() => {
    if (!statusQuery.data) return
    const needsChanged = prevNeedsConnectionsRef.current !== statusQuery.data.needs_connections
    prevNeedsConnectionsRef.current = statusQuery.data.needs_connections
    const step = resolveActiveStep(statusQuery.data.connections)
    const allOk = allConnectionsOk(statusQuery.data.connections)
    setActive((current) => {
      if (current === SERVICE_ORDER.length) return current
      if (allOk) return step
      if (!statusQuery.data.needs_connections && !needsChanged) return current
      return step
    })
  }, [statusQuery.data])

  function refreshStatus() {
    void queryClient.invalidateQueries({ queryKey: ["connections", "status"] })
  }

  const clearAll = useMutation({
    mutationFn: clearAllConnections,
    onSuccess: () => {
      setActive(0)
      refreshStatus()
      showToast({ color: "green", message: "All connections cleared" })
    },
    onError: (error: unknown) => {
      showToast({
        color: "red",
        message: error instanceof ApiError ? String(error.message) : "Could not clear connections",
      })
    },
  })

  function handleConnectionCleared() {
    refreshStatus()
  }

  function handleGoToDashboard() {
    navigate("/", { replace: true })
  }

  function handleClearAll() {
    const confirmed = window.confirm("Remove all saved Plex, Trakt, Letterboxd, and TMDB connections? You will need to set them up again.")
    if (confirmed) clearAll.mutate()
  }

  if (statusQuery.isLoading) {
    return <Text>Loading connections…</Text>
  }

  const connections = statusQuery.data?.connections ?? []
  const hasConfiguredConnections = connections.some((item) => item.status !== "unconfigured")

  function connectionFor(service: Service) {
    return connections.find((item) => item.service === service)
  }

  return (
    <Stack gap="md" maw={{ base: "100%", lg: "85%" }} mx="auto">
      <Title order={3}>{needsConnections ? "Connect your services" : "Connections"}</Title>
      <Text c="dimmed" size="sm">
        {needsConnections
          ? "Configure Plex, Trakt, Letterboxd, and TMDB before running sync jobs."
          : "Manage Plex, Trakt, Letterboxd, and TMDB credentials for sync jobs."}
      </Text>

      {!needsConnections && hasConfiguredConnections ? (
        <Group justify="flex-end" wrap="wrap">
          <Button variant="outline" color="red" leftSection={<TrashIcon />} onClick={handleClearAll} loading={clearAll.isPending}>
            Clear all connections
          </Button>
        </Group>
      ) : null}

      <Stepper
        active={active}
        onStepClick={setActive}
        orientation={isNarrow ? "vertical" : "horizontal"}
        classNames={{
          stepIcon: classes.stepIcon,
          stepCompletedIcon: classes.stepCompletedIcon,
        }}
      >
        <Stepper.Step
          classNames={{ stepIcon: stepIconClass(connectionFor("plex")) }}
          icon={<ServiceLogo service="plex" size={18} />}
          completedIcon={<ServiceLogo service="plex" size={18} />}
          label={<ServiceStepLabel service="plex" connection={connectionFor("plex")} />}
          description="Plex account"
        >
          <PlexStep
            connection={connectionFor("plex")}
            onSaved={() => {
              refreshStatus()
              setActive(1)
            }}
            onCleared={handleConnectionCleared}
          />
        </Stepper.Step>
        <Stepper.Step
          classNames={{ stepIcon: stepIconClass(connectionFor("trakt")) }}
          icon={<ServiceLogo service="trakt" size={18} />}
          completedIcon={<ServiceLogo service="trakt" size={18} />}
          label={<ServiceStepLabel service="trakt" connection={connectionFor("trakt")} />}
          description="Device OAuth"
        >
          <TraktStep
            connection={connectionFor("trakt")}
            onSaved={() => {
              refreshStatus()
              setActive(2)
            }}
            onCleared={handleConnectionCleared}
          />
        </Stepper.Step>
        <Stepper.Step
          classNames={{ stepIcon: stepIconClass(connectionFor("letterboxd")) }}
          icon={<ServiceLogo service="letterboxd" size={18} />}
          completedIcon={<ServiceLogo service="letterboxd" size={18} />}
          label={<ServiceStepLabel service="letterboxd" connection={connectionFor("letterboxd")} />}
          description="Read-only login"
        >
          <LetterboxdStep
            connection={connectionFor("letterboxd")}
            onSaved={() => {
              refreshStatus()
              setActive(3)
            }}
            onCleared={handleConnectionCleared}
          />
        </Stepper.Step>
        <Stepper.Step
          classNames={{ stepIcon: stepIconClass(connectionFor("tmdb")) }}
          icon={<ServiceLogo service="tmdb" size={18} />}
          completedIcon={<ServiceLogo service="tmdb" size={18} />}
          label={<ServiceStepLabel service="tmdb" connection={connectionFor("tmdb")} />}
          description="API key"
        >
          <TmdbStep
            connection={connectionFor("tmdb")}
            onSaved={() => {
              refreshStatus()
              setActive(SERVICE_ORDER.length)
            }}
            onCleared={handleConnectionCleared}
          />
        </Stepper.Step>

        <Stepper.Completed>
          <FinishedStep onGoToDashboard={handleGoToDashboard} />
        </Stepper.Completed>
      </Stepper>
    </Stack>
  )
}
