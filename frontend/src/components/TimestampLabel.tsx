import { Group, Popover, Stack, Text, UnstyledButton } from "@mantine/core"
import { useInterval } from "@mantine/hooks"
import { useState } from "react"

import { CopyAction } from "src/components/CopyAction"
import { useDisplayPreferences } from "src/settings/DisplayPreferencesProvider"
import { formatDateTime, formatRelativeTime, formatScheduleDateTime } from "src/utils/dateTimeFormat"

type TimestampVariant = "datetime" | "schedule"

interface TimestampLabelProps {
  value: string | null | undefined
  variant?: TimestampVariant
  /** When true, show relative only; click for absolute time (copyable). */
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
      <Popover width="auto" position="bottom-start" withArrow shadow="sm">
        <Popover.Target>
          <UnstyledButton aria-label={`Full timestamp: ${absolute}`} title="Click for full timestamp" style={{ width: "fit-content" }}>
            <Text size={size} c="dimmed">
              {relative ?? absolute}
            </Text>
          </UnstyledButton>
        </Popover.Target>
        <Popover.Dropdown p="xs">
          <Group gap={4} wrap="nowrap">
            <Text size="sm" style={{ userSelect: "all" }}>
              {absolute}
            </Text>
            <CopyAction value={absolute} label="Copy timestamp" />
          </Group>
        </Popover.Dropdown>
      </Popover>
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
