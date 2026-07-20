import { Box, Button, Group, Modal, Skeleton, Stack, Table, Text, Title } from "@mantine/core"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useState } from "react"
import { Link } from "react-router-dom"

import { ApiError } from "src/api/client"
import { cloneJob, deleteJob, listJobs } from "src/api/jobApi"
import type { Job } from "src/api/jobs"
import { DATA_TYPE_LABELS, SOURCE_PAIR_LABELS } from "src/api/jobs"
import { EmptyState } from "src/components/EmptyState"
import { PlusIcon } from "src/components/icons/PlusIcon"
import { DryRunBadge, JobStatusBadge } from "src/components/JobForm/JobForm"
import { JobActions } from "src/components/jobs/JobActions"
import { JobListCard } from "src/components/jobs/JobListCard"
import { ListPageSkeleton } from "src/components/loading/PageSkeletons"
import { DataTypeBadge } from "src/components/services/DataTypeBadge"
import { SourcePairLabel } from "src/components/services/SourcePairLabel"
import { RoundedTable } from "src/components/table/RoundedTable"
import { SortableTh } from "src/components/table/SortableTh"
import { sortedColumnCellClass } from "src/components/table/sortedColumnCellClass"
import { TimestampLabel } from "src/components/TimestampLabel"
import { useRunJob } from "src/hooks/useRunJob"
import dryRunRowClasses from "src/styles/dryRunRow.module.css"
import { showToast } from "src/toast"
import { nextSortState, sortRows, type SortState } from "src/utils/tableSort"

type JobSortColumn = "name" | "source_pair" | "data_types" | "cron" | "dry_run" | "enabled"

function ScheduleCell({ job }: { job: Job }) {
  return (
    <Stack gap={2}>
      <Text size="sm" ff="monospace">
        {job.cron}
      </Text>
      {!job.enabled ? (
        <Text size="xs" c="dimmed">
          Disabled — no next run
        </Text>
      ) : job.next_run_at ? (
        <TimestampLabel value={job.next_run_at} variant="schedule" size="xs" />
      ) : (
        <Text size="xs" c="dimmed">
          Next run unavailable
        </Text>
      )}
    </Stack>
  )
}

export function JobsPage() {
  const queryClient = useQueryClient()
  const [sort, setSort] = useState<SortState<JobSortColumn> | null>(null)
  const [jobPendingDelete, setJobPendingDelete] = useState<Job | null>(null)
  const { isRunning, onRun } = useRunJob()
  const jobsQuery = useQuery({
    queryKey: ["jobs"],
    queryFn: listJobs,
  })

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
      <Stack gap="md">
        <Group justify="space-between" wrap="wrap" gap="sm">
          <Title order={3}>Sync jobs</Title>
          <Skeleton height={36} width={110} radius="xl" />
        </Group>
        <ListPageSkeleton />
      </Stack>
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
    <Stack gap="md" maw={{ base: "100%", lg: "85%" }} mx="auto">
      <Group justify="space-between" wrap="wrap" gap="sm">
        <Title order={3}>Sync jobs</Title>
        <Button component={Link} to="/jobs/new" leftSection={<PlusIcon />}>
          New job
        </Button>
      </Group>

      {jobs.length === 0 ? (
        <EmptyState>
          <Text c="dimmed">No jobs yet. Create one to start syncing on a schedule.</Text>
        </EmptyState>
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
                    onRun={onRun}
                    onClone={(j) => cloneMutation.mutate(j)}
                    clonePending={cloneMutation.isPending && cloneMutation.variables?.id === job.id}
                    onDelete={setJobPendingDelete}
                  />
                }
              />
            ))}
          </Stack>

          <Box visibleFrom="sm">
            <RoundedTable striped highlightOnHover minWidth={800}>
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
                          <DataTypeBadge key={dt} dataType={dt} mode="responsive" />
                        ))}
                      </Group>
                    </Table.Td>
                    <Table.Td className={sortedColumnCellClass(sort, "cron")}>
                      <ScheduleCell job={job} />
                    </Table.Td>
                    <Table.Td className={sortedColumnCellClass(sort, "dry_run")}>
                      <DryRunBadge dryRun={job.dry_run} compact mode="responsive" />
                    </Table.Td>
                    <Table.Td className={sortedColumnCellClass(sort, "enabled")}>
                      <JobStatusBadge enabled={job.enabled} mode="responsive" />
                    </Table.Td>
                    <Table.Td>
                      <JobActions
                        job={job}
                        isRunning={isRunning}
                        onRun={onRun}
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
