import { Badge, Group, Paper, Stack, Text } from "@mantine/core"
import { Link } from "react-router-dom"

import type { Job } from "src/api/jobs"
import type { RunListItem } from "src/api/runs"
import { TimestampLabel } from "src/components/TimestampLabel"
import { aggregateGlanceStats, type GlanceWindow } from "src/utils/runGlanceStats"

interface DashboardGlanceStripProps {
  jobs: Job[]
  runs: RunListItem[]
}

function WindowStats({ label, window, jobs, runs }: { label: string; window: GlanceWindow; jobs: Job[]; runs: RunListItem[] }) {
  const stats = aggregateGlanceStats(jobs, runs, window)
  return (
    <Stack gap={6}>
      <Text size="xs" c="dimmed" tt="uppercase" fw={600}>
        {label}
      </Text>
      <Group gap="xs" wrap="wrap">
        <Badge component={Link} to="/runs?status=success" variant="light" color="green" style={{ cursor: "pointer" }}>
          {stats.success} ok
        </Badge>
        <Badge component={Link} to="/runs?status=failed" variant="light" color="red" style={{ cursor: "pointer" }}>
          {stats.failed} failed
        </Badge>
        <Badge component={Link} to="/runs?status=partial" variant="light" color="orange" style={{ cursor: "pointer" }}>
          {stats.partial} partial
        </Badge>
        {stats.running > 0 ? (
          <Badge component={Link} to="/runs?status=running" variant="light" color="blue" style={{ cursor: "pointer" }}>
            {stats.running} running
          </Badge>
        ) : null}
        <Badge variant="outline" color="gray">
          {stats.planned} planned
        </Badge>
      </Group>
    </Stack>
  )
}

export function DashboardGlanceStrip({ jobs, runs }: DashboardGlanceStripProps) {
  const nextRunAt = aggregateGlanceStats(jobs, runs, "7d").nextRunAt

  return (
    <Paper withBorder radius="md" p="md">
      <Group justify="space-between" align="flex-start" wrap="wrap" gap="lg">
        <WindowStats label="Last 24 hours" window="24h" jobs={jobs} runs={runs} />
        <WindowStats label="Last 7 days" window="7d" jobs={jobs} runs={runs} />
        <Stack gap={6}>
          <Text size="xs" c="dimmed" tt="uppercase" fw={600}>
            Next scheduled
          </Text>
          {nextRunAt ? (
            <TimestampLabel value={nextRunAt} variant="schedule" size="sm" />
          ) : (
            <Text size="sm" c="dimmed">
              None
            </Text>
          )}
        </Stack>
      </Group>
    </Paper>
  )
}
