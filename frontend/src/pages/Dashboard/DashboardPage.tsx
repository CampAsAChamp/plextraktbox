import { ActionIcon, Alert, Badge, Box, Button, Group, Loader, Stack, Table, Text, Title, Tooltip } from "@mantine/core"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useState } from "react"
import { Link } from "react-router-dom"

import { ApiError } from "src/api/client"
import type { ConnectionSummary } from "src/api/connections"
import { listJobs, runJob } from "src/api/jobApi"
import type { Job } from "src/api/jobs"
import { ConnectionStatusBadge } from "src/components/connections/ConnectionStatusBadge"
import { ConnectIcon } from "src/components/icons/ConnectIcon"
import { ListIcon } from "src/components/icons/ListIcon"
import { PencilIcon } from "src/components/icons/PencilIcon"
import { PlusIcon } from "src/components/icons/PlusIcon"
import { DryRunBadge, JobStatusBadge } from "src/components/JobForm/JobForm"
import { JobListCard } from "src/components/jobs/JobListCard"
import { RunStatusBadge } from "src/components/runs/RunBadges"
import { RunSummaryStats } from "src/components/runs/RunSummaryStats"
import { SourcePairLabel } from "src/components/services/SourcePairLabel"
import { RoundedTable } from "src/components/table/RoundedTable"
import { useDisplayPreferences } from "src/settings/DisplayPreferencesProvider"
import dryRunRowClasses from "src/styles/dryRunRow.module.css"
import { showToast } from "src/toast"
import { formatDateTime, formatScheduleDateTime } from "src/utils/dateTimeFormat"

interface DashboardPageProps {
  connections?: ConnectionSummary[]
}

type RunMode = "run" | "dry-run"

/** Stable key for the current set of failed/partial last runs. */
function problemJobsSignature(jobs: Job[]): string {
  return jobs
    .map((job) => `${job.id}:${job.last_run?.id ?? 0}:${job.last_run?.status ?? ""}`)
    .sort()
    .join("|")
}

function ScheduleCell({ job }: { job: Job }) {
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

function LastRunCell({ job }: { job: Job }) {
  const { preferences } = useDisplayPreferences()
  const last = job.last_run
  if (!last) {
    return (
      <Text size="sm" c="dimmed">
        Never run
      </Text>
    )
  }

  return (
    <Stack gap={2}>
      <Group gap="xs">
        <Button component={Link} to={`/runs/${last.id}`} variant="subtle" size="compact-xs" p={0}>
          #{last.id}
        </Button>
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

function jobActions(job: Job, isRunning: (job: Job, mode: RunMode) => boolean, onRun: (job: Job, mode: RunMode) => void) {
  return (
    <Group gap={4} wrap="wrap">
      <Tooltip label="Run now">
        <ActionIcon variant="light" aria-label={`Run ${job.name}`} loading={isRunning(job, "run")} onClick={() => onRun(job, "run")}>
          ▶
        </ActionIcon>
      </Tooltip>
      <Tooltip label="Dry-run">
        <ActionIcon
          variant="light"
          color="blue"
          aria-label={`Dry-run ${job.name}`}
          loading={isRunning(job, "dry-run")}
          onClick={() => onRun(job, "dry-run")}
        >
          ▷
        </ActionIcon>
      </Tooltip>
      <Tooltip label="Edit">
        <ActionIcon component={Link} to={`/jobs/${job.id}/edit`} variant="subtle" aria-label={`Edit ${job.name}`}>
          <PencilIcon />
        </ActionIcon>
      </Tooltip>
    </Group>
  )
}

export function DashboardPage({ connections = [] }: DashboardPageProps) {
  const queryClient = useQueryClient()
  const [dismissedProblemsKey, setDismissedProblemsKey] = useState<string | null>(null)

  const jobsQuery = useQuery({
    queryKey: ["jobs"],
    queryFn: listJobs,
  })

  const runMutation = useMutation({
    mutationFn: ({ job, mode }: { job: Job; mode: RunMode }) => runJob(job.id, mode === "dry-run" ? true : undefined),
    onSuccess: (run) => {
      void queryClient.invalidateQueries({ queryKey: ["jobs"] })
      void queryClient.invalidateQueries({ queryKey: ["runs"] })
      showToast({
        color: run.status === "success" ? "green" : "orange",
        message: `Run #${run.id} finished with status ${run.status}`,
      })
    },
    onError: (error: unknown) => {
      const message = error instanceof ApiError ? String(error.message) : "Run failed"
      showToast({ color: "red", message })
    },
  })

  const needsReauth = connections.some((item) => item.status === "needs_reauth")
  const jobs = jobsQuery.data ?? []
  const problemJobs = jobs.filter((job) => job.last_run?.status === "failed" || job.last_run?.status === "partial")
  const problemsKey = problemJobsSignature(problemJobs)
  const showProblemsAlert = problemJobs.length > 0 && problemsKey !== "" && problemsKey !== dismissedProblemsKey

  function isRunning(job: Job, mode: RunMode): boolean {
    return runMutation.isPending && runMutation.variables?.job.id === job.id && runMutation.variables.mode === mode
  }

  function onRun(job: Job, mode: RunMode) {
    runMutation.mutate({ job, mode })
  }

  return (
    <Stack gap="lg" maw={{ base: "100%", lg: "85%" }} mx="auto">
      <Group justify="space-between" align="flex-start" wrap="wrap" gap="sm">
        <Stack gap={4}>
          <Title order={3}>Dashboard</Title>
        </Stack>
        <Button component={Link} to="/jobs/new" leftSection={<PlusIcon />}>
          New job
        </Button>
      </Group>

      {needsReauth ? (
        <Alert color="orange" title="Re-authorization required">
          <Stack gap="xs">
            <Text size="sm">One or more service connections need attention. Update credentials to resume sync jobs.</Text>
            <Button component={Link} to="/connections" variant="light" size="xs" w="fit-content" leftSection={<ConnectIcon />}>
              Manage connections
            </Button>
          </Stack>
        </Alert>
      ) : null}

      {showProblemsAlert ? (
        <Alert
          color="red"
          title="Attention needed"
          withCloseButton
          closeButtonLabel="Dismiss attention banner"
          onClose={() => setDismissedProblemsKey(problemsKey)}
        >
          <Stack gap="sm">
            {problemJobs.map((job) => (
              <Group key={job.id} gap="sm" wrap="wrap">
                <Text size="sm" fw={500}>
                  {job.name}
                </Text>
                {job.last_run ? (
                  <>
                    <RunStatusBadge status={job.last_run.status} />
                    <Button component={Link} to={`/runs/${job.last_run.id}`} variant="subtle" size="compact-xs">
                      View run #{job.last_run.id}
                    </Button>
                  </>
                ) : null}
              </Group>
            ))}
          </Stack>
        </Alert>
      ) : null}

      <Stack gap="xs">
        <Text fw={500}>Connections</Text>
        <Group gap="xs" wrap="wrap">
          {connections.map((item) => (
            <ConnectionStatusBadge key={item.service} connection={item} />
          ))}
        </Group>
        <Button component={Link} to="/connections" variant="subtle" size="xs" w="fit-content" leftSection={<ConnectIcon />}>
          Manage connections
        </Button>
      </Stack>

      <Stack gap="sm">
        <Group justify="space-between" wrap="wrap" gap="sm">
          <Group gap="sm">
            <Text fw={500}>Jobs</Text>
            <Badge color="blue" variant="filled">
              {jobs.length}
            </Badge>
          </Group>
          <Button component={Link} to="/jobs" size="xs" leftSection={<ListIcon />}>
            Manage jobs
          </Button>
        </Group>

        {jobsQuery.isLoading ? (
          <Group>
            <Loader size="sm" />
            <Text size="sm">Loading jobs…</Text>
          </Group>
        ) : jobsQuery.isError ? (
          <Text c="red" size="sm">
            Could not load jobs.
          </Text>
        ) : jobs.length === 0 ? (
          <Text c="dimmed" size="sm">
            No jobs yet.{" "}
            <Text component={Link} to="/jobs/new" span c="blue">
              Create your first job
            </Text>
            .
          </Text>
        ) : (
          <>
            <Stack gap="sm" hiddenFrom="sm">
              {jobs.map((job) => (
                <JobListCard key={job.id} job={job} showLastRun actions={jobActions(job, isRunning, onRun)} />
              ))}
            </Stack>

            <Box visibleFrom="sm">
              <RoundedTable striped highlightOnHover minWidth={960}>
                <Table.Thead>
                  <Table.Tr>
                    <Table.Th>Name</Table.Th>
                    <Table.Th>Job Type</Table.Th>
                    <Table.Th>Schedule</Table.Th>
                    <Table.Th>Dry run</Table.Th>
                    <Table.Th>Status</Table.Th>
                    <Table.Th>Last run</Table.Th>
                    <Table.Th>Actions</Table.Th>
                  </Table.Tr>
                </Table.Thead>
                <Table.Tbody>
                  {jobs.map((job) => (
                    <Table.Tr key={job.id} className={job.dry_run ? dryRunRowClasses.dryRunRow : undefined}>
                      <Table.Td>
                        <Text fw={500}>{job.name}</Text>
                      </Table.Td>
                      <Table.Td>
                        <SourcePairLabel sourcePair={job.source_pair} variant="icons" />
                      </Table.Td>
                      <Table.Td>
                        <ScheduleCell job={job} />
                      </Table.Td>
                      <Table.Td>
                        <DryRunBadge dryRun={job.dry_run} compact />
                      </Table.Td>
                      <Table.Td>
                        <JobStatusBadge enabled={job.enabled} />
                      </Table.Td>
                      <Table.Td>
                        <LastRunCell job={job} />
                      </Table.Td>
                      <Table.Td>{jobActions(job, isRunning, onRun)}</Table.Td>
                    </Table.Tr>
                  ))}
                </Table.Tbody>
              </RoundedTable>
            </Box>
          </>
        )}
      </Stack>
    </Stack>
  )
}
