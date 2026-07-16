import { Accordion, Alert, Button, Group, List, PasswordInput, Stack, Text } from "@mantine/core"
import { useMutation } from "@tanstack/react-query"
import { useEffect, useState } from "react"
import { z } from "zod"

import { ApiError } from "src/api/client"
import type { ConnectionSummary, TmdbConnectionInput } from "src/api/connections"
import { saveTmdbConnection, testTmdbConnection } from "src/api/connectionsApi"
import {
  isConnectionConfigured,
  SAVED_SECRET_PLACEHOLDER,
  secretPlaceholderInputProps,
} from "src/components/connections/connectionFormHelpers"
import { TestConnectionButton, useConnectionTestFeedback } from "src/components/connections/connectionTestFeedback"
import { ClearConnectionButton } from "src/components/connections/steps/ClearConnectionButton"
import { FieldLabel } from "src/components/connections/steps/FieldLabel"
import { KeyIcon } from "src/components/icons/KeyIcon"
import { SaveIcon } from "src/components/icons/SaveIcon"
import { showToast } from "src/toast"

const tmdbSchema = z.object({
  api_key: z.string().min(1, "API key is required"),
})

const TMDB_API_SETTINGS_URL = "https://www.themoviedb.org/settings/api"

function TmdbApiKeyHelpContent() {
  return (
    <Stack gap="xs">
      <List size="sm" spacing="xs">
        <List.Item>
          Sign in or create a free account at{" "}
          <a href="https://www.themoviedb.org/" target="_blank" rel="noreferrer">
            themoviedb.org
          </a>
        </List.Item>
        <List.Item>
          Open{" "}
          <a href={TMDB_API_SETTINGS_URL} target="_blank" rel="noreferrer">
            Account Settings → API
          </a>
        </List.Item>
        <List.Item>
          Click <strong>Request an API Key</strong>, choose <strong>Developer</strong>, and complete the application form
        </List.Item>
        <List.Item>
          Copy the <strong>API Key</strong> (v3 auth) — not the Read Access Token
        </List.Item>
      </List>
      <Button component="a" href={TMDB_API_SETTINGS_URL} target="_blank" rel="noreferrer" variant="light" size="xs" w="fit-content">
        Open TMDB API settings
      </Button>
    </Stack>
  )
}

function TmdbApiKeyHelp({
  collapsible,
  expanded,
  onExpandedChange,
}: {
  collapsible: boolean
  expanded: boolean
  onExpandedChange: (next: boolean) => void
}) {
  if (!collapsible) {
    return (
      <Alert color="blue" title="Get a TMDB API key">
        <TmdbApiKeyHelpContent />
      </Alert>
    )
  }

  return (
    <Alert
      color="blue"
      p={0}
      styles={{
        root: { overflow: "hidden" },
        message: { margin: 0 },
      }}
    >
      <Accordion
        chevronPosition="right"
        onChange={(value) => onExpandedChange(value === "help")}
        styles={{
          chevron: { color: "var(--mantine-color-blue-light-color)" },
          control: { padding: "var(--mantine-spacing-md)" },
          label: { color: "var(--mantine-color-blue-light-color)", fontWeight: 600 },
          panel: { padding: "0 var(--mantine-spacing-md) var(--mantine-spacing-md)" },
        }}
        value={expanded ? "help" : null}
        variant="unstyled"
      >
        <Accordion.Item style={{ border: "none" }} value="help">
          <Accordion.Control>Get a TMDB API key</Accordion.Control>
          <Accordion.Panel>
            <TmdbApiKeyHelpContent />
          </Accordion.Panel>
        </Accordion.Item>
      </Accordion>
    </Alert>
  )
}

export function TmdbStep({
  connection,
  onSaved,
  onCleared,
}: {
  connection: ConnectionSummary | undefined
  onSaved: () => void
  onCleared: () => void
}) {
  const configured = isConnectionConfigured(connection)
  const baselineApiKey = configured ? SAVED_SECRET_PLACEHOLDER : ""

  const [apiKey, setApiKey] = useState(baselineApiKey)
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [showTmdbHelp, setShowTmdbHelp] = useState(!configured)

  useEffect(() => {
    const nextConfigured = isConnectionConfigured(connection)
    setApiKey(nextConfigured ? SAVED_SECRET_PLACEHOLDER : "")
    setErrors({})
    setShowTmdbHelp(!nextConfigured)
  }, [connection?.service, connection?.status])

  const isDirty = apiKey !== baselineApiKey
  const { testStatus, onTestSuccess, onTestError, resetTestStatus } = useConnectionTestFeedback()

  useEffect(() => {
    resetTestStatus()
  }, [connection?.service, connection?.status, resetTestStatus])

  useEffect(() => {
    if (isDirty) resetTestStatus()
  }, [isDirty, resetTestStatus])

  const save = useMutation({
    mutationFn: (body: TmdbConnectionInput) => saveTmdbConnection(body),
    onSuccess: () => {
      showToast({ color: "green", message: "TMDB connected" })
      onSaved()
    },
    onError: (error: unknown) => {
      showToast({
        color: "red",
        message: error instanceof ApiError ? String(error.message) : "TMDB setup failed",
      })
    },
  })

  const testSaved = useMutation({
    mutationFn: () => testTmdbConnection(),
    onSuccess: onTestSuccess,
    onError: (error: unknown) => onTestError(error, "TMDB test failed"),
  })

  const testDraft = useMutation({
    mutationFn: (body: TmdbConnectionInput) => testTmdbConnection(body),
    onSuccess: onTestSuccess,
    onError: (error: unknown) => onTestError(error, "TMDB test failed"),
  })

  function handleTest() {
    if (!isDirty && configured) {
      testSaved.mutate()
      return
    }
    if (!apiKey.trim() || apiKey === SAVED_SECRET_PLACEHOLDER) return
    testDraft.mutate({ api_key: apiKey.trim() })
  }

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault()
    const parsed = tmdbSchema.safeParse({ api_key: apiKey })
    if (!parsed.success || apiKey === SAVED_SECRET_PLACEHOLDER) {
      const fieldErrors: Record<string, string> = {}
      if (!apiKey.trim() || apiKey === SAVED_SECRET_PLACEHOLDER) {
        fieldErrors.api_key = "API key is required"
      }
      for (const issue of parsed.error?.issues ?? []) {
        const key = issue.path[0]
        if (typeof key === "string") fieldErrors[key] = issue.message
      }
      setErrors(fieldErrors)
      return
    }
    setErrors({})
    save.mutate(parsed.data)
  }

  const canTest = configured && !isDirty ? true : apiKey.trim() !== "" && apiKey !== SAVED_SECRET_PLACEHOLDER

  return (
    <form onSubmit={handleSubmit}>
      <Stack gap="sm">
        <Text c="dimmed" size="sm">
          TMDB helps match titles across Plex, Trakt, and Letterboxd.
        </Text>
        {connection?.status === "ok" ? (
          <Alert color="green" title="TMDB connected">
            <Text size="sm">API key saved and ready for title matching.</Text>
          </Alert>
        ) : null}
        <TmdbApiKeyHelp collapsible={configured} expanded={showTmdbHelp} onExpandedChange={setShowTmdbHelp} />
        <PasswordInput
          label={<FieldLabel icon={<KeyIcon />}>TMDB API key</FieldLabel>}
          onChange={(event) => setApiKey(event.currentTarget.value)}
          error={errors.api_key}
          {...secretPlaceholderInputProps(
            apiKey,
            setApiKey,
            configured,
            "Saved API key hidden",
            "Saved on the server — enter a new API key to replace it.",
          )}
        />
        <Group wrap="wrap">
          <Button type="submit" loading={save.isPending} disabled={!isDirty} leftSection={<SaveIcon />}>
            Save TMDB connection
          </Button>
          <TestConnectionButton
            testStatus={testStatus}
            onClick={handleTest}
            loading={testSaved.isPending || testDraft.isPending}
            disabled={!canTest}
          />
          <ClearConnectionButton service="tmdb" connection={connection} onCleared={onCleared} />
        </Group>
      </Stack>
    </form>
  )
}
