import {
  ActionIcon,
  Alert,
  Button,
  Group,
  Loader,
  Select,
  SimpleGrid,
  Stack,
  Table,
  Text,
  Title,
  Tooltip,
} from "@mantine/core";
import { useQuery } from "@tanstack/react-query";
import { useLocation, useNavigate, useSearchParams } from "react-router-dom";
import { listJobs } from "../api/jobApi";
import { listRuns } from "../api/runs";
import {
  RUN_TRIGGER_OPTIONS,
  filterRuns,
  parseRunStatuses,
  parseRunTrigger,
} from "../utils/runFilters";
import {
  DryRunBadge,
  renderRunTriggerOption,
  RunStatusBadge,
  RunTriggerBadge,
} from "../components/runs/RunBadges";
import { RunStatusMultiSelect } from "../components/runs/RunStatusMultiSelect";
import { useDisplayPreferences } from "../settings/DisplayPreferencesProvider";
import { formatDateTime } from "../utils/dateTimeFormat";
import dryRunRowClasses from "../styles/dryRunRow.module.css";
import classes from "./RunHistoryPage.module.css";

function StrokeIcon({
  size = 14,
  className,
  children,
}: {
  size?: number;
  className?: string;
  children: React.ReactNode;
}) {
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
  );
}

function RefreshIcon({ spinning = false }: { spinning?: boolean }) {
  return (
    <StrokeIcon className={spinning ? classes.spin : undefined}>
      <path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8" />
      <path d="M3 3v5h5" />
      <path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16" />
      <path d="M16 16h5v5" />
    </StrokeIcon>
  );
}

export function RunHistoryPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const { preferences } = useDisplayPreferences();
  const [searchParams, setSearchParams] = useSearchParams();
  const jobIdParam = searchParams.get("job_id");
  const jobId = jobIdParam && !Number.isNaN(Number(jobIdParam)) ? Number(jobIdParam) : undefined;
  const statusFilters = parseRunStatuses(searchParams.get("status"));
  const triggerFilter = parseRunTrigger(searchParams.get("trigger"));
  const hasFilters = jobId !== undefined || statusFilters.length > 0 || triggerFilter !== undefined;

  const jobsQuery = useQuery({
    queryKey: ["jobs"],
    queryFn: listJobs,
  });

  const runsQuery = useQuery({
    queryKey: ["runs", { job_id: jobId }],
    queryFn: () => listRuns({ job_id: jobId, limit: 100 }),
  });

  function updateSearchParam(key: string, value: string | null) {
    const next = new URLSearchParams(searchParams);
    if (value) {
      next.set(key, value);
    } else {
      next.delete(key);
    }
    setSearchParams(next);
  }

  function updateSearchParamList(key: string, values: string[]) {
    const next = new URLSearchParams(searchParams);
    if (values.length > 0) {
      next.set(key, values.join(","));
    } else {
      next.delete(key);
    }
    setSearchParams(next);
  }

  const isRefreshing = runsQuery.isFetching || jobsQuery.isFetching;

  function refreshRuns() {
    void Promise.all([runsQuery.refetch(), jobsQuery.refetch()]);
  }

  if (runsQuery.isLoading || jobsQuery.isLoading) {
    return (
      <Group>
        <Loader size="sm" />
        <Text>Loading run history…</Text>
      </Group>
    );
  }

  if (runsQuery.isError) {
    return <Text c="red">Could not load runs.</Text>;
  }

  const jobs = jobsQuery.data ?? [];
  const selectedJob = jobId !== undefined ? jobs.find((job) => job.id === jobId) : undefined;
  const deletedJob = jobId !== undefined && selectedJob === undefined;
  const allRuns = runsQuery.data?.items ?? [];
  const runs = filterRuns(allRuns, { statuses: statusFilters, trigger: triggerFilter });
  const deletedJobName = allRuns.find((run) => run.job_id === jobId)?.job_name ?? null;

  const jobOptions = [
    { value: "", label: "All jobs" },
    ...jobs.map((job) => ({ value: String(job.id), label: job.name })),
  ];

  return (
    <Stack gap="md">
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
        <Tooltip label="Refresh runs">
          <ActionIcon
            variant="light"
            aria-label="Refresh runs"
            disabled={isRefreshing}
            onClick={refreshRuns}
          >
            <RefreshIcon spinning={isRefreshing} />
          </ActionIcon>
        </Tooltip>
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
          renderOption={renderRunTriggerOption}
          leftSection={triggerFilter ? <RunTriggerBadge trigger={triggerFilter} /> : undefined}
          leftSectionPointerEvents="none"
          leftSectionWidth={triggerFilter ? 104 : undefined}
          styles={triggerFilter ? { input: { color: "transparent" } } : undefined}
        />
      </SimpleGrid>

      {hasFilters ? (
        <Group gap="sm">
          <Button
            variant="subtle"
            size="compact-sm"
            onClick={() => setSearchParams({})}
          >
            Clear filters
          </Button>
          <Text size="sm" c="dimmed">
            Showing {runs.length} of {allRuns.length} runs
          </Text>
        </Group>
      ) : null}

      {runs.length === 0 ? (
        <Text c="dimmed">
          {allRuns.length === 0
            ? deletedJob
              ? "No runs were recorded for this deleted job."
              : "No runs yet. Run a job manually or wait for the scheduler."
            : "No runs match the current filters."}
        </Text>
      ) : (
        <Table striped highlightOnHover>
          <Table.Thead>
            <Table.Tr>
              <Table.Th>Run</Table.Th>
              <Table.Th>Job</Table.Th>
              <Table.Th>Trigger</Table.Th>
              <Table.Th>Dry run</Table.Th>
              <Table.Th>Status</Table.Th>
              <Table.Th>Started</Table.Th>
              <Table.Th>Duration</Table.Th>
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {runs.map((run) => {
              const started = new Date(run.started_at);
              const finished = run.finished_at ? new Date(run.finished_at) : null;
              const durationMs = finished ? finished.getTime() - started.getTime() : null;
              const duration =
                durationMs === null ? "running…" : durationMs < 1000 ? "<1s" : `${Math.round(durationMs / 1000)}s`;

              const runsListPath = `${location.pathname}${location.search}`;

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
                      event.preventDefault();
                      navigate(`/runs/${run.id}`, { state: { from: runsListPath } });
                    }
                  }}
                >
                  <Table.Td>
                    <Text fw={500}>#{run.id}</Text>
                  </Table.Td>
                  <Table.Td>{run.job_name ?? `Job #${run.job_id}`}</Table.Td>
                  <Table.Td>
                    <RunTriggerBadge trigger={run.trigger} />
                  </Table.Td>
                  <Table.Td>
                    <DryRunBadge dryRun={run.dry_run} compact />
                  </Table.Td>
                  <Table.Td>
                    <RunStatusBadge status={run.status} />
                  </Table.Td>
                  <Table.Td>{formatDateTime(run.started_at, preferences)}</Table.Td>
                  <Table.Td>{duration}</Table.Td>
                </Table.Tr>
              );
            })}
          </Table.Tbody>
        </Table>
      )}
    </Stack>
  );
}
