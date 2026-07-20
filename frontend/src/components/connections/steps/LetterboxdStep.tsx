import { Accordion, Alert, Badge, Button, Group, NumberInput, PasswordInput, Stack, Text, TextInput } from "@mantine/core"
import { useMutation } from "@tanstack/react-query"
import { useEffect, useState } from "react"

import { ApiError } from "src/api/client"
import type { ConnectionSummary, LetterboxdConnectionInput } from "src/api/connections"
import { saveLetterboxdConnection, testLetterboxdConnection } from "src/api/connectionsApi"
import {
  isConnectionConfigured,
  SAVED_SECRET_PLACEHOLDER,
  savedUsername,
  secretPlaceholderInputProps,
} from "src/components/connections/connectionFormHelpers"
import { TestConnectionButton } from "src/components/connections/connectionTestFeedback"
import { ClearConnectionButton } from "src/components/connections/steps/ClearConnectionButton"
import { FieldLabel } from "src/components/connections/steps/FieldLabel"
import { useConnectionTestFeedback } from "src/components/connections/useConnectionTestFeedback"
import { LockIcon } from "src/components/icons/LockIcon"
import { SaveIcon } from "src/components/icons/SaveIcon"
import { UserIcon } from "src/components/icons/UserIcon"
import { showToast } from "src/toast"

const FLARESOLVERR_ACCORDION = "flaresolverr"

function savedFlaresolverrUrl(connection: ConnectionSummary | undefined): string {
  if (!isConnectionConfigured(connection)) return ""
  const value = connection?.config.flaresolverr_url
  return typeof value === "string" ? value : ""
}

function savedFlaresolverrTimeoutMs(connection: ConnectionSummary | undefined): number | string {
  if (!isConnectionConfigured(connection)) return ""
  const value = connection?.config.flaresolverr_timeout_ms
  return typeof value === "number" ? value : ""
}

function hasFlaresolverrConfig(url: string, timeoutMs: number | string): boolean {
  return url.trim() !== "" || typeof timeoutMs === "number"
}

export function LetterboxdStep({
  connection,
  onSaved,
  onCleared,
}: {
  connection: ConnectionSummary | undefined
  onSaved: () => void
  onCleared: () => void
}) {
  const configured = isConnectionConfigured(connection)
  const baselineUsername = savedUsername(connection)
  const baselinePassword = configured ? SAVED_SECRET_PLACEHOLDER : ""
  const baselineFlaresolverrUrl = savedFlaresolverrUrl(connection)
  const baselineFlaresolverrTimeoutMs = savedFlaresolverrTimeoutMs(connection)
  const baselineHasFlaresolverr = hasFlaresolverrConfig(baselineFlaresolverrUrl, baselineFlaresolverrTimeoutMs)

  const [username, setUsername] = useState(baselineUsername)
  const [password, setPassword] = useState(baselinePassword)
  const [flaresolverrUrl, setFlaresolverrUrl] = useState(baselineFlaresolverrUrl)
  const [flaresolverrTimeoutMs, setFlaresolverrTimeoutMs] = useState<number | string>(baselineFlaresolverrTimeoutMs)
  const [flaresolverrOpen, setFlaresolverrOpen] = useState(baselineHasFlaresolverr)
  const [errors, setErrors] = useState<Record<string, string>>({})

  useEffect(() => {
    setUsername(baselineUsername)
    setPassword(baselinePassword)
    setFlaresolverrUrl(baselineFlaresolverrUrl)
    setFlaresolverrTimeoutMs(baselineFlaresolverrTimeoutMs)
    setFlaresolverrOpen(baselineHasFlaresolverr)
    setErrors({})
  }, [baselineUsername, baselinePassword, baselineFlaresolverrUrl, baselineFlaresolverrTimeoutMs, baselineHasFlaresolverr])

  const isDirty =
    username !== baselineUsername ||
    password !== baselinePassword ||
    flaresolverrUrl !== baselineFlaresolverrUrl ||
    flaresolverrTimeoutMs !== baselineFlaresolverrTimeoutMs
  const { testStatus, onTestSuccess, onTestError, resetTestStatus } = useConnectionTestFeedback()

  useEffect(() => {
    resetTestStatus()
  }, [connection?.service, connection?.status, resetTestStatus])

  useEffect(() => {
    if (isDirty) resetTestStatus()
  }, [isDirty, resetTestStatus])

  const save = useMutation({
    mutationFn: (body: LetterboxdConnectionInput) => saveLetterboxdConnection(body),
    onSuccess: () => {
      showToast({ color: "green", message: "Letterboxd connected" })
      onSaved()
    },
    onError: (error: unknown) => {
      showToast({
        color: "red",
        message: error instanceof ApiError ? String(error.message) : "Letterboxd setup failed",
      })
    },
  })

  const testSaved = useMutation({
    mutationFn: () => testLetterboxdConnection(),
    onSuccess: onTestSuccess,
    onError: (error: unknown) => onTestError(error, "Letterboxd test failed"),
  })

  const testDraft = useMutation({
    mutationFn: (body: LetterboxdConnectionInput) => testLetterboxdConnection(body),
    onSuccess: onTestSuccess,
    onError: (error: unknown) => onTestError(error, "Letterboxd test failed"),
  })

  function buildPayload(): LetterboxdConnectionInput | null {
    if (!username.trim()) return null
    const payload: LetterboxdConnectionInput = { username: username.trim() }
    if (password && password !== SAVED_SECRET_PLACEHOLDER) {
      payload.password = password
    } else if (!configured) {
      return null
    }
    const url = flaresolverrUrl.trim()
    payload.flaresolverr_url = url || null
    if (typeof flaresolverrTimeoutMs === "number" && Number.isFinite(flaresolverrTimeoutMs)) {
      payload.flaresolverr_timeout_ms = flaresolverrTimeoutMs
    } else {
      payload.flaresolverr_timeout_ms = null
    }
    return payload
  }

  function handleTest() {
    if (!isDirty && configured) {
      testSaved.mutate()
      return
    }
    const payload = buildPayload()
    if (!payload) return
    testDraft.mutate(payload)
  }

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault()
    const payload = buildPayload()
    if (!payload) {
      const fieldErrors: Record<string, string> = {}
      if (!username.trim()) fieldErrors.username = "Username is required"
      if (!configured && (!password || password === SAVED_SECRET_PLACEHOLDER)) {
        fieldErrors.password = "Password is required"
      }
      setErrors(fieldErrors)
      return
    }
    if (flaresolverrTimeoutMs !== "" && (typeof flaresolverrTimeoutMs !== "number" || flaresolverrTimeoutMs < 1000)) {
      setFlaresolverrOpen(true)
      setErrors({ flaresolverr_timeout_ms: "Timeout must be at least 1000 ms" })
      return
    }
    setErrors({})
    save.mutate(payload)
  }

  const canTest =
    username.trim() !== "" &&
    (configured
      ? password === SAVED_SECRET_PLACEHOLDER || password.trim() !== ""
      : password.trim() !== "" && password !== SAVED_SECRET_PLACEHOLDER)
  const flaresolverrConfigured = hasFlaresolverrConfig(flaresolverrUrl, flaresolverrTimeoutMs)

  return (
    <form onSubmit={handleSubmit}>
      <Stack gap="sm">
        <Text c="dimmed" size="sm">
          Letterboxd is read-only. Your credentials are used to scrape your diary and ratings.
        </Text>
        {connection?.status === "ok" ? (
          <Alert color="green" title="Letterboxd connected">
            <Text size="sm">
              Signed in as <strong>{savedUsername(connection)}</strong>.
            </Text>
          </Alert>
        ) : null}
        <TextInput
          label={<FieldLabel icon={<UserIcon />}>Letterboxd username</FieldLabel>}
          value={username}
          onChange={(event) => setUsername(event.currentTarget.value)}
          error={errors.username}
        />
        <PasswordInput
          label={<FieldLabel icon={<LockIcon />}>Letterboxd password</FieldLabel>}
          onChange={(event) => setPassword(event.currentTarget.value)}
          error={errors.password}
          {...secretPlaceholderInputProps(
            password,
            setPassword,
            configured,
            "Saved password hidden",
            "Saved on the server — enter a new password to replace it.",
          )}
        />
        <Accordion
          variant="contained"
          chevronPosition="left"
          value={flaresolverrOpen ? FLARESOLVERR_ACCORDION : null}
          onChange={(value) => setFlaresolverrOpen(value === FLARESOLVERR_ACCORDION)}
        >
          <Accordion.Item value={FLARESOLVERR_ACCORDION}>
            <Accordion.Control>
              <Group gap="sm">
                <Text fw={500}>Cloudflare / FlareSolverr</Text>
                {flaresolverrConfigured ? (
                  <Badge variant="light" size="sm">
                    Configured
                  </Badge>
                ) : null}
              </Group>
            </Accordion.Control>
            <Accordion.Panel>
              <Stack gap="sm">
                <Text size="sm" c="dimmed">
                  Skip this unless Letterboxd connection tests fail with a Cloudflare challenge — typically{" "}
                  <Text span fw={500} inherit>
                    403 Forbidden
                  </Text>{" "}
                  or a “Just a moment…” page (not a normal wrong-password error). FlareSolverr clears that challenge before login; its URL
                  must be reachable from the plextraktbox container.
                </Text>
                <TextInput
                  label="FlareSolverr URL"
                  description="Optional. Example: http://192.168.1.105:8191"
                  placeholder="http://192.168.1.105:8191"
                  value={flaresolverrUrl}
                  onChange={(event) => setFlaresolverrUrl(event.currentTarget.value)}
                />
                <NumberInput
                  label="FlareSolverr timeout (ms)"
                  description="Optional. Leave empty to use the server default (60000)."
                  placeholder="60000"
                  min={1000}
                  step={1000}
                  value={flaresolverrTimeoutMs}
                  onChange={setFlaresolverrTimeoutMs}
                  error={errors.flaresolverr_timeout_ms}
                />
              </Stack>
            </Accordion.Panel>
          </Accordion.Item>
        </Accordion>
        <Group wrap="wrap">
          <Button type="submit" loading={save.isPending} disabled={!isDirty} leftSection={<SaveIcon />}>
            Save Letterboxd connection
          </Button>
          <TestConnectionButton
            testStatus={testStatus}
            onClick={handleTest}
            loading={testSaved.isPending || testDraft.isPending}
            disabled={!canTest}
          />
          <ClearConnectionButton service="letterboxd" connection={connection} onCleared={onCleared} />
        </Group>
      </Stack>
    </form>
  )
}
