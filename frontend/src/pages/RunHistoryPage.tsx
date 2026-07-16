import { ActionIcon, Alert, Box, Button, Group, Select, SimpleGrid, Stack, Table, Text, Title } from "@mantine/core"
import { useQuery } from "@tanstack/react-query"
import { useState } from "react"
import { useLocation, useNavigate, useSearchParams } from "react-router-dom"

import { listJobs } from "src/api/jobApi"
import type { RunListItem } from "src/api/jobs"
import { SOURCE_PAIR_LABELS } from "src/api/jobs"
import { listRuns } from "src/api/runs"
import { EmptyState } from "src/components/EmptyState"
import { FiltersSkeleton, ListPageSkeleton } from "src/components/loading/PageSkeletons"
import { DryRunBadge, RunStatusBadge, RunTriggerBadge } from "src/components/runs/RunBadges"
import { RunListCard } from "src/components/runs/RunListCard"
import { RunStatusMultiSelect } from "src/components/runs/RunStatusMultiSelect"
import { SourcePairLabel } from "src/components/services/SourcePairLabel"
import { RoundedTable } from "src/components/table/RoundedTable"
import { SortableTh } from "src/components/table/SortableTh"
import { sortedColumnCellClass } from "src/components/table/sortedColumnCellClass"
import { TimestampLabel } from "src/components/TimestampLabel"
import classes from "src/pages/RunHistoryPage.module.css"
import dryRunRowClasses from "src/styles/dryRunRow.module.css"
import { showToast } from "src/toast"
import { formatDuration } from "src/utils/dateTimeFormat"
import { filterRuns, parseRunStatuses, parseRunTrigger, RUN_TRIGGER_OPTIONS } from "src/utils/runFilters"
import { nextSortState, sortRows, type SortState } from "src/utils/tableSort"

/** One full rotation of `.spin` — keeps the icon visible on fast local refetches. */
const MIN_REFRESH_SPIN_MS = 800

type RunSortColumn = "id" | "job_name" | "source_pair" | "trigger" | "dry_run" | "status" | "started_at" | "duration"

function runDurationMs(run: RunListItem): number | null {
  if (!run.finished_at) {
    return null
  }
  return new Date(run.finished_at).getTime() - new Date(run.started_at).getTime()
}

function StrokeIcon({ size = 14, className, children }: { size?: number; className?: string; children: React.ReactNode }) {
  return (
    <svg
      className={className}
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

function RefreshIcon({ spinning = false }: { spinning?: boolean }) {
  return (
    <StrokeIcon className={spinning ? classes.spin : undefined}>
      <path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8" />
      <path d="M3 3v5h5" />
      <path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16" />
      <path d="M16 16h5v5" />
    </StrokeIcon>
  )
}

export function RunHistoryPage() {
  const location = useLocation()
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const [sort, setSort] = useState<SortState<RunSortColumn> | null>(null)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const jobIdParam = searchParams.get("job_id")
  const jobId = jobIdParam && !Number.isNaN(Number(jobIdParam)) ? Number(jobIdParam) : undefined
  const statusFilters = parseRunStatuses(searchParams.get("status"))
  const triggerFilter = parseRunTrigger(searchParams.get("trigger"))
  const hasFilters = jobId !== undefined || statusFilters.length > 0 || triggerFilter !== undefined

  const jobsQuery = useQuery({
    queryKey: ["jobs"],
    queryFn: listJobs,
  })

  const runsQuery = useQuery({
    queryKey: ["runs", { job_id: jobId }],
    queryFn: () => listRuns({ job_id: jobId, limit: 100 }),
  })

  function updateSearchParam(key: string, value: string | null) {
    const next = new URLSearchParams(searchParams)
    if (value) {
      next.set(key, value)
    } else {
      next.delete(key)
    }
    setSearchParams(next)
  }

  function updateSearchParamList(key: string, values: string[]) {
    const next = new URLSearchParams(searchParams)
    if (values.length > 0) {
      next.set(key, values.join(","))
    } else {
      next.delete(key)
    }
    setSearchParams(next)
  }

  async function refreshRuns() {
    if (isRefreshing) return
    setIsRefreshing(true)
    const started = performance.now()
    try {
      const [runsResult, jobsResult] = await Promise.all([runsQuery.refetch(), jobsQuery.refetch()])
      const error = runsResult.error ?? jobsResult.error
      if (error) {
        const message = error instanceof Error ? error.message : "Failed to refresh runs"
        showToast({ color: "red", message })
        return
      }
      showToast({ color: "green", message: "Runs refreshed" })
    } finally {
      const remaining = Math.max(0, MIN_REFRESH_SPIN_MS - (performance.now() - started))
      if (remaining > 0) {
        await new Promise<void>((resolve) => {
          window.setTimeout(resolve, remaining)
        })
      }
      setIsRefreshing(false)
    }
  }

  if (runsQuery.isLoading || jobsQuery.isLoading) {
    return (
      <Stack gap="md">
        <Group justify="space-between" wrap="wrap" gap="sm">
          <Title order={3}>Run history</Title>
        </Group>
        <FiltersSkeleton />
        <ListPageSkeleton />
      </Stack>
    )
  }

  if (runsQuery.isError) {
    return <Text c="red">Could not load runs.</Text>
  }

  const jobs = jobsQuery.data ?? []
  const selectedJob = jobId !== undefined ? jobs.find((job) => job.id === jobId) : undefined
  const deletedJob = jobId !== undefined && selectedJob === undefined
  const allRuns = runsQuery.data?.items ?? []
  const runs = sortRows(filterRuns(allRuns, { statuses: statusFilters, trigger: triggerFilter }), sort, {
    id: (run) => run.id,
    job_name: (run) => run.job_name ?? `Job #${run.job_id}`,
    source_pair: (run) => (run.source_pair ? SOURCE_PAIR_LABELS[run.source_pair] : null),
    trigger: (run) => run.trigger,
    dry_run: (run) => run.dry_run,
    status: (run) => run.status,
    started_at: (run) => new Date(run.started_at).getTime(),
    duration: (run) => runDurationMs(run),
  })
  const deletedJobName = allRuns.find((run) => run.job_id === jobId)?.job_name ?? null

  const jobOptions = [{ value: "", label: "All jobs" }, ...jobs.map((job) => ({ value: String(job.id), label: job.name }))]

  function handleSort(column: RunSortColumn) {
    setSort((current) => nextSortState(current, column))
  }

  return (
    <Stack gap="md" maw={{ base: "100%", lg: "85%" }} mx="auto">
      <Group gap="sm">
        <Title order={3}>
          {selectedJob
            ? `Runs for ${selectedJob.name}`
            : deletedJob
              ? deletedJobName
                ? `Runs for ${deletedJobName} (deleted)`
                : `Runs for deleted job #${jobId}`
              : jobId
                ? `Runs for job #${jobId}`
                : "Run history"}
        </Title>
        <ActionIcon variant="light" size="lg" miw={44} h={44} aria-label="Refresh runs" disabled={isRefreshing} onClick={refreshRuns}>
          <RefreshIcon spinning={isRefreshing} />
        </ActionIcon>
      </Group>

      {deletedJob ? (
        <Alert color="yellow" title="Job deleted">
          This job no longer exists. Showing historical runs only.
        </Alert>
      ) : null}

      <SimpleGrid cols={{ base: 1, sm: 3 }} spacing="md">
        <Select
          label="Job"
          data={jobOptions}
          value={jobId !== undefined ? String(jobId) : ""}
          onChange={(value) => updateSearchParam("job_id", value || null)}
          searchable
          styles={{
            input: { cursor: "pointer" },
            section: { cursor: "pointer" },
          }}
        />
        <RunStatusMultiSelect
          label="Status"
          value={statusFilters}
          onChange={(values) => updateSearchParamList("status", values)}
          clearable
        />
        <Select
          label="Trigger"
          data={RUN_TRIGGER_OPTIONS.map((option) => ({ value: option.value, label: option.value }))}
          value={triggerFilter ?? null}
          onChange={(value) => updateSearchParam("trigger", value)}
          clearable
          placeholder="All triggers"
          renderOption={({ option }) => <RunTriggerBadge trigger={option.value} />}
          leftSection={triggerFilter ? <RunTriggerBadge trigger={triggerFilter} /> : undefined}
          leftSectionPointerEvents="none"
          leftSectionWidth={triggerFilter ? 104 : undefined}
          styles={triggerFilter ? { input: { color: "transparent" } } : undefined}
        />
      </SimpleGrid>

      {hasFilters ? (
        <Group gap="sm">
          <Button variant="subtle" size="compact-sm" onClick={() => setSearchParams({})}>
            Clear filters
          </Button>
          <Text size="sm" c="dimmed">
            Showing {runs.length} of {allRuns.length} runs
          </Text>
        </Group>
      ) : null}

      {runs.length === 0 ? (
        <EmptyState>
          <Text c="dimmed">
            {allRuns.length === 0
              ? deletedJob
                ? "No runs were recorded for this deleted job."
                : "No runs yet. Run a job manually or wait for the scheduler."
              : "No runs match the current filters."}
          </Text>
        </EmptyState>
      ) : (
        <>
          <Stack gap="sm" hiddenFrom="sm">
            {runs.map((run) => {
              const runsListPath = `${location.pathname}${location.search}`
              return <RunListCard key={run.id} run={run} onOpen={() => navigate(`/runs/${run.id}`, { state: { from: runsListPath } })} />
            })}
          </Stack>

          <Box visibleFrom="sm">
            <RoundedTable striped highlightOnHover minWidth={900}>
              <Table.Thead>
                <Table.Tr>
                  <SortableTh column="id" label="Run" sort={sort} onSort={handleSort} />
                  <SortableTh column="job_name" label="Job" sort={sort} onSort={handleSort} />
                  <SortableTh column="source_pair" label="Job Type" sort={sort} onSort={handleSort} />
                  <SortableTh column="trigger" label="Trigger" sort={sort} onSort={handleSort} />
                  <SortableTh column="dry_run" label="Dry run" sort={sort} onSort={handleSort} />
                  <SortableTh column="status" label="Status" sort={sort} onSort={handleSort} />
                  <SortableTh column="started_at" label="Started" sort={sort} onSort={handleSort} />
                  <SortableTh column="duration" label="Duration" sort={sort} onSort={handleSort} />
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {runs.map((run) => {
                  const durationMs = runDurationMs(run)
                  const duration = durationMs === null ? "running…" : formatDuration(durationMs)

                  const runsListPath = `${location.pathname}${location.search}`

                  return (
                    <Table.Tr
                      key={run.id}
                      className={run.dry_run ? dryRunRowClasses.dryRunRow : undefined}
                      tabIndex={0}
                      aria-label={`Run #${run.id} for ${run.job_name ?? `job #${run.job_id}`}`}
                      style={{ cursor: "pointer" }}
                      onClick={() => navigate(`/runs/${run.id}`, { state: { from: runsListPath } })}
                      onKeyDown={(event) => {
                        if (event.key === "Enter" || event.key === " ") {
                          event.preventDefault()
                          navigate(`/runs/${run.id}`, { state: { from: runsListPath } })
                        }
                      }}
                    >
                      <Table.Td className={sortedColumnCellClass(sort, "id")}>
                        <Text fw={500}>#{run.id}</Text>
                      </Table.Td>
                      <Table.Td className={sortedColumnCellClass(sort, "job_name")}>{run.job_name ?? `Job #${run.job_id}`}</Table.Td>
                      <Table.Td className={sortedColumnCellClass(sort, "source_pair")}>
                        {run.source_pair ? <SourcePairLabel sourcePair={run.source_pair} variant="icons" /> : <Text c="dimmed">—</Text>}
                      </Table.Td>
                      <Table.Td className={sortedColumnCellClass(sort, "trigger")}>
                        <RunTriggerBadge trigger={run.trigger} />
                      </Table.Td>
                      <Table.Td className={sortedColumnCellClass(sort, "dry_run")}>
                        <DryRunBadge dryRun={run.dry_run} compact />
                      </Table.Td>
                      <Table.Td className={sortedColumnCellClass(sort, "status")}>
                        <RunStatusBadge status={run.status} />
                      </Table.Td>
                      <Table.Td className={sortedColumnCellClass(sort, "started_at")}>
                        <TimestampLabel value={run.started_at} size="xs" />
                      </Table.Td>
                      <Table.Td className={sortedColumnCellClass(sort, "duration")}>{duration}</Table.Td>
                    </Table.Tr>
                  )
                })}
              </Table.Tbody>
            </RoundedTable>
          </Box>
        </>
      )}
    </Stack>
  )
}
