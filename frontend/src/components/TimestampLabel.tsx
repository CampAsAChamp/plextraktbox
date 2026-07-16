import { Stack, Text } from "@mantine/core"
import { useInterval } from "@mantine/hooks"
import { useState } from "react"

import { useDisplayPreferences } from "src/settings/DisplayPreferencesProvider"
import { formatDateTime, formatRelativeTime, formatScheduleDateTime } from "src/utils/dateTimeFormat"

type TimestampVariant = "datetime" | "schedule"

interface TimestampLabelProps {
  value: string | null | undefined
  variant?: TimestampVariant
  /** When true, omit absolute line and show relative only (still refreshes). */
  relativeOnly?: boolean
  size?: "xs" | "sm"
}

export function TimestampLabel({ value, variant = "datetime", relativeOnly = false, size = "sm" }: TimestampLabelProps) {
  const { preferences } = useDisplayPreferences()
  const [, setTick] = useState(0)
  useInterval(() => setTick((n) => n + 1), 60_000)

  if (!value) {
    return (
      <Text size={size} c="dimmed">
        —
      </Text>
    )
  }

  const absolute = variant === "schedule" ? formatScheduleDateTime(value, preferences) : formatDateTime(value, preferences)
  const relative = formatRelativeTime(value)

  if (relativeOnly) {
    return (
      <Text size={size} c="dimmed">
        {relative ?? absolute}
      </Text>
    )
  }

  return (
    <Stack gap={2}>
      <Text size={size}>{absolute}</Text>
      {relative ? (
        <Text size="xs" c="dimmed">
          {relative}
        </Text>
      ) : null}
    </Stack>
  )
}
