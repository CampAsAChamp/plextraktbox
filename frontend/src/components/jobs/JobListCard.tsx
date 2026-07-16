import { Box, Group, Paper, Stack, Text, useMantineTheme } from "@mantine/core"
import type { ReactNode } from "react"
import { Link } from "react-router-dom"

import type { Job } from "src/api/jobs"
import { DryRunBadge, JobStatusBadge } from "src/components/JobForm/JobForm"
import { RunStatusBadge } from "src/components/runs/RunBadges"
import { RunSummaryStats } from "src/components/runs/RunSummaryStats"
import { DataTypeBadge } from "src/components/services/DataTypeBadge"
import { SourcePairLabel } from "src/components/services/SourcePairLabel"
import { useDisplayPreferences } from "src/settings/DisplayPreferencesProvider"
import dryRunRowClasses from "src/styles/dryRunRow.module.css"
import { formatDateTime, formatScheduleDateTime } from "src/utils/dateTimeFormat"

type JobListCardProps = {
  job: Job
  /** Icon action buttons (Run, Edit, …). */
  actions: ReactNode
  /** When true, show last-run summary (Dashboard). */
  showLastRun?: boolean
}

function ScheduleSummary({ job }: { job: Job }) {
  const { preferences } = useDisplayPreferences()
  const nextLabel = !job.enabled
    ? "Disabled — no next run"
    : job.next_run_at
      ? formatScheduleDateTime(job.next_run_at, preferences)
      : "Next run unavailable"

  return (
    <Stack gap={2}>
      <Text size="sm" ff="monospace">
        {job.cron}
      </Text>
      <Text size="xs" c="dimmed">
        {nextLabel}
      </Text>
    </Stack>
  )
}

function LastRunSummary({ job }: { job: Job }) {
  const { preferences } = useDisplayPreferences()
  const theme = useMantineTheme()
  const last = job.last_run
  if (!last) {
    return (
      <Text size="sm" c="dimmed">
        Never run
      </Text>
    )
  }

  return (
    <Stack gap={4}>
      <Group gap="xs" wrap="wrap">
        <Text component={Link} to={`/runs/${last.id}`} size="sm" fw={500} c={`${theme.primaryColor}.4`} style={{ textDecoration: "none" }}>
          Run #{last.id}
        </Text>
        <RunStatusBadge status={last.status} />
        <DryRunBadge dryRun={last.dry_run} />
      </Group>
      <Text size="xs" c="dimmed">
        {formatDateTime(last.finished_at ?? last.started_at, preferences)}
      </Text>
      <RunSummaryStats matched={last.matched} added={last.added} errors={last.errors} />
    </Stack>
  )
}

/** Mobile job card — used below `sm` on Jobs and Dashboard. */
export function JobListCard({ job, actions, showLastRun = false }: JobListCardProps) {
  return (
    <Paper withBorder radius="lg" p="md" className={job.dry_run ? dryRunRowClasses.dryRunRow : undefined}>
      <Stack gap="sm">
        <Group justify="space-between" align="flex-start" wrap="nowrap" gap="sm">
          <Stack gap={6} style={{ flex: 1, minWidth: 0 }}>
            <Text fw={600} size="md" style={{ wordBreak: "break-word" }}>
              {job.name}
            </Text>
            <Group gap="xs" wrap="wrap">
              <JobStatusBadge enabled={job.enabled} />
              <DryRunBadge dryRun={job.dry_run} />
            </Group>
          </Stack>
          <Box style={{ flexShrink: 0 }}>{actions}</Box>
        </Group>

        <Stack gap={4}>
          <Text size="xs" c="dimmed" tt="uppercase" fw={600}>
            Job type
          </Text>
          <SourcePairLabel sourcePair={job.source_pair} variant="icons" />
        </Stack>

        <Stack gap={4}>
          <Text size="xs" c="dimmed" tt="uppercase" fw={600}>
            Data
          </Text>
          <Group gap={4} wrap="wrap">
            {job.data_types.map((dt) => (
              <DataTypeBadge key={dt} dataType={dt} />
            ))}
          </Group>
        </Stack>

        <Stack gap={4}>
          <Text size="xs" c="dimmed" tt="uppercase" fw={600}>
            Schedule
          </Text>
          <ScheduleSummary job={job} />
        </Stack>

        {showLastRun ? (
          <Stack gap={4}>
            <Text size="xs" c="dimmed" tt="uppercase" fw={600}>
              Last run
            </Text>
            <LastRunSummary job={job} />
          </Stack>
        ) : null}
      </Stack>
    </Paper>
  )
}
