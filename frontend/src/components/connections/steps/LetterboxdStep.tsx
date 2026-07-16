import { Alert, Button, Group, PasswordInput, Stack, Text, TextInput } from "@mantine/core"
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

  const [username, setUsername] = useState(baselineUsername)
  const [password, setPassword] = useState(baselinePassword)
  const [errors, setErrors] = useState<Record<string, string>>({})

  useEffect(() => {
    setUsername(baselineUsername)
    setPassword(baselinePassword)
    setErrors({})
  }, [baselineUsername, baselinePassword])

  const isDirty = username !== baselineUsername || password !== baselinePassword
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
    setErrors({})
    save.mutate(payload)
  }

  const canTest =
    username.trim() !== "" &&
    (configured
      ? password === SAVED_SECRET_PLACEHOLDER || password.trim() !== ""
      : password.trim() !== "" && password !== SAVED_SECRET_PLACEHOLDER)

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
