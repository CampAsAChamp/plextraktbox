import { ActionIcon, Box, Button, Group, Loader, Modal, Stack, Table, Text, Title, Tooltip } from "@mantine/core"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useState } from "react"
import { Link } from "react-router-dom"

import { ApiError } from "src/api/client"
import { cloneJob, deleteJob, listJobs, runJob } from "src/api/jobApi"
import type { Job } from "src/api/jobs"
import { DATA_TYPE_LABELS, SOURCE_PAIR_LABELS } from "src/api/jobs"
import { PencilIcon } from "src/components/icons/PencilIcon"
import { PlusIcon } from "src/components/icons/PlusIcon"
import { TrashIcon } from "src/components/icons/TrashIcon"
import { DryRunBadge, JobStatusBadge } from "src/components/JobForm/JobForm"
import { JobListCard } from "src/components/jobs/JobListCard"
import { DataTypeBadge } from "src/components/services/DataTypeBadge"
import { SourcePairLabel } from "src/components/services/SourcePairLabel"
import { RoundedTable } from "src/components/table/RoundedTable"
import { SortableTh } from "src/components/table/SortableTh"
import { sortedColumnCellClass } from "src/components/table/sortedColumnCellClass"
import { useDisplayPreferences } from "src/settings/DisplayPreferencesProvider"
import dryRunRowClasses from "src/styles/dryRunRow.module.css"
import { showToast } from "src/toast"
import { formatScheduleDateTime } from "src/utils/dateTimeFormat"
import { nextSortState, sortRows, type SortState } from "src/utils/tableSort"

type JobSortColumn = "name" | "source_pair" | "data_types" | "cron" | "dry_run" | "enabled"
type RunMode = "run" | "dry-run"

function StrokeIcon({ size = 14, children }: { size?: number; children: React.ReactNode }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden
    >
      {children}
    </svg>
  )
}

function HistoryIcon() {
  return (
    <StrokeIcon>
      <path d="M12 8v4l3 3" />
      <path d="M3.05 11a9 9 0 1 1 .5 4" />
      <path d="M3 4v5h5" />
    </StrokeIcon>
  )
}

function CloneIcon() {
  return (
    <StrokeIcon>
      <rect x="9" y="9" width="13" height="13" rx="2" />
      <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
    </StrokeIcon>
  )
}

type JobActionsProps = {
  job: Job
  isRunning: (job: Job, mode: RunMode) => boolean
  onRun: (job: Job, mode: RunMode) => void
  onClone: (job: Job) => void
  clonePending: boolean
  onDelete: (job: Job) => void
}

function JobActions({ job, isRunning, onRun, onClone, clonePending, onDelete }: JobActionsProps) {
  return (
    <Group gap={4} wrap="wrap">
      <Tooltip label="Run now">
        <ActionIcon variant="light" aria-label="Run now" loading={isRunning(job, "run")} onClick={() => onRun(job, "run")}>
          ▶
        </ActionIcon>
      </Tooltip>
      <Tooltip label="Dry-run">
        <ActionIcon
          variant="light"
          color="blue"
          aria-label="Dry-run"
          loading={isRunning(job, "dry-run")}
          onClick={() => onRun(job, "dry-run")}
        >
          ▷
        </ActionIcon>
      </Tooltip>
      <Tooltip label="Edit">
        <ActionIcon component={Link} to={`/jobs/${job.id}/edit`} variant="subtle" aria-label="Edit">
          <PencilIcon />
        </ActionIcon>
      </Tooltip>
      <Tooltip label="Clone">
        <ActionIcon variant="subtle" aria-label="Clone" loading={clonePending} onClick={() => onClone(job)}>
          <CloneIcon />
        </ActionIcon>
      </Tooltip>
      <Tooltip label="History">
        <ActionIcon component={Link} to={`/runs?job_id=${job.id}`} variant="subtle" aria-label="History">
          <HistoryIcon />
        </ActionIcon>
      </Tooltip>
      <Tooltip label="Delete">
        <ActionIcon color="red" variant="subtle" aria-label="Delete" onClick={() => onDelete(job)}>
          <TrashIcon />
        </ActionIcon>
      </Tooltip>
    </Group>
  )
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

export function JobsPage() {
  const queryClient = useQueryClient()
  const [sort, setSort] = useState<SortState<JobSortColumn> | null>(null)
  const [jobPendingDelete, setJobPendingDelete] = useState<Job | null>(null)
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

  function isRunning(job: Job, mode: RunMode): boolean {
    return runMutation.isPending && runMutation.variables?.job.id === job.id && runMutation.variables.mode === mode
  }

  const cloneMutation = useMutation({
    mutationFn: (job: Job) => cloneJob(job.id),
    onSuccess: (cloned) => {
      void queryClient.invalidateQueries({ queryKey: ["jobs"] })
      showToast({
        color: "green",
        message: `Cloned as "${cloned.name}" (disabled)`,
      })
    },
    onError: (error: unknown) => {
      const message = error instanceof ApiError ? String(error.message) : "Clone failed"
      showToast({ color: "red", message })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (jobId: number) => deleteJob(jobId),
    onSuccess: () => {
      setJobPendingDelete(null)
      void queryClient.invalidateQueries({ queryKey: ["jobs"] })
      showToast({ color: "green", message: "Job deleted" })
    },
    onError: (error: unknown) => {
      const message = error instanceof ApiError ? String(error.message) : "Delete failed"
      showToast({ color: "red", message })
    },
  })

  if (jobsQuery.isLoading) {
    return (
      <Group>
        <Loader size="sm" />
        <Text>Loading jobs…</Text>
      </Group>
    )
  }

  if (jobsQuery.isError) {
    return <Text c="red">Could not load jobs.</Text>
  }

  const jobs = sortRows(jobsQuery.data ?? [], sort, {
    name: (job) => job.name,
    source_pair: (job) => SOURCE_PAIR_LABELS[job.source_pair],
    data_types: (job) =>
      job.data_types
        .map((dt) => DATA_TYPE_LABELS[dt])
        .slice()
        .sort((a, b) => a.localeCompare(b))
        .join(", "),
    cron: (job) => job.cron,
    dry_run: (job) => job.dry_run,
    enabled: (job) => job.enabled,
  })

  function handleSort(column: JobSortColumn) {
    setSort((current) => nextSortState(current, column))
  }

  return (
    <Stack gap="md">
      <Group justify="space-between" wrap="wrap" gap="sm">
        <Title order={3}>Sync jobs</Title>
        <Button component={Link} to="/jobs/new" leftSection={<PlusIcon />}>
          New job
        </Button>
      </Group>

      {jobs.length === 0 ? (
        <Text c="dimmed">No jobs yet. Create one to start syncing on a schedule.</Text>
      ) : (
        <>
          <Stack gap="sm" hiddenFrom="sm">
            {jobs.map((job) => (
              <JobListCard
                key={job.id}
                job={job}
                actions={
                  <JobActions
                    job={job}
                    isRunning={isRunning}
                    onRun={(j, mode) => runMutation.mutate({ job: j, mode })}
                    onClone={(j) => cloneMutation.mutate(j)}
                    clonePending={cloneMutation.isPending && cloneMutation.variables?.id === job.id}
                    onDelete={setJobPendingDelete}
                  />
                }
              />
            ))}
          </Stack>

          <Box visibleFrom="sm">
            <RoundedTable striped highlightOnHover minWidth={900}>
              <Table.Thead>
                <Table.Tr>
                  <SortableTh column="name" label="Name" sort={sort} onSort={handleSort} />
                  <SortableTh column="source_pair" label="Job Type" sort={sort} onSort={handleSort} />
                  <SortableTh column="data_types" label="Data" sort={sort} onSort={handleSort} />
                  <SortableTh column="cron" label="Schedule" sort={sort} onSort={handleSort} />
                  <SortableTh column="dry_run" label="Dry run" sort={sort} onSort={handleSort} />
                  <SortableTh column="enabled" label="Status" sort={sort} onSort={handleSort} />
                  <Table.Th>Actions</Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {jobs.map((job) => (
                  <Table.Tr key={job.id} className={job.dry_run ? dryRunRowClasses.dryRunRow : undefined}>
                    <Table.Td className={sortedColumnCellClass(sort, "name")}>
                      <Text fw={500}>{job.name}</Text>
                    </Table.Td>
                    <Table.Td className={sortedColumnCellClass(sort, "source_pair")}>
                      <SourcePairLabel sourcePair={job.source_pair} variant="icons" />
                    </Table.Td>
                    <Table.Td className={sortedColumnCellClass(sort, "data_types")}>
                      <Group gap={4}>
                        {job.data_types.map((dt) => (
                          <DataTypeBadge key={dt} dataType={dt} />
                        ))}
                      </Group>
                    </Table.Td>
                    <Table.Td className={sortedColumnCellClass(sort, "cron")}>
                      <ScheduleCell job={job} />
                    </Table.Td>
                    <Table.Td className={sortedColumnCellClass(sort, "dry_run")}>
                      <DryRunBadge dryRun={job.dry_run} compact />
                    </Table.Td>
                    <Table.Td className={sortedColumnCellClass(sort, "enabled")}>
                      <JobStatusBadge enabled={job.enabled} />
                    </Table.Td>
                    <Table.Td>
                      <JobActions
                        job={job}
                        isRunning={isRunning}
                        onRun={(j, mode) => runMutation.mutate({ job: j, mode })}
                        onClone={(j) => cloneMutation.mutate(j)}
                        clonePending={cloneMutation.isPending && cloneMutation.variables?.id === job.id}
                        onDelete={setJobPendingDelete}
                      />
                    </Table.Td>
                  </Table.Tr>
                ))}
              </Table.Tbody>
            </RoundedTable>
          </Box>
        </>
      )}

      <Modal
        opened={jobPendingDelete !== null}
        onClose={() => {
          if (!deleteMutation.isPending) {
            setJobPendingDelete(null)
          }
        }}
        title="Delete job"
        centered
      >
        <Stack gap="md">
          <Text size="sm">
            Delete{" "}
            <Text span fw={600}>
              {jobPendingDelete?.name}
            </Text>
            ? Scheduled runs will stop. Past run history is kept.
          </Text>
          <Group justify="flex-end" gap="sm">
            <Button variant="default" disabled={deleteMutation.isPending} onClick={() => setJobPendingDelete(null)}>
              Cancel
            </Button>
            <Button
              color="red"
              loading={deleteMutation.isPending}
              onClick={() => {
                if (jobPendingDelete) {
                  deleteMutation.mutate(jobPendingDelete.id)
                }
              }}
            >
              Delete
            </Button>
          </Group>
        </Stack>
      </Modal>
    </Stack>
  )
}
