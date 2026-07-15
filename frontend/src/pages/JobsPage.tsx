import {
  ActionIcon,
  Button,
  Group,
  Loader,
  Stack,
  Table,
  Text,
  Title,
  Tooltip,
} from "@mantine/core";
import { notifications } from "@mantine/notifications";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link } from "react-router-dom";
import type { Job } from "../api/jobs";
import { DATA_TYPE_LABELS, SOURCE_PAIR_LABELS } from "../api/jobs";
import { DataTypeBadge } from "../components/services/DataTypeBadge";
import { SourcePairLabel } from "../components/services/SourcePairLabel";
import { SortableTh, sortedColumnCellClass } from "../components/table/SortableTh";
import { ApiError } from "../api/client";
import { deleteJob, listJobs, runJob } from "../api/jobApi";
import { DryRunBadge, JobStatusBadge } from "../components/JobForm/JobForm";
import { TrashIcon } from "../components/icons/TrashIcon";
import { useDisplayPreferences } from "../settings/DisplayPreferencesProvider";
import { formatScheduleDateTime } from "../utils/dateTimeFormat";
import { nextSortState, sortRows, type SortState } from "../utils/tableSort";
import dryRunRowClasses from "../styles/dryRunRow.module.css";

type JobSortColumn = "name" | "source_pair" | "data_types" | "cron" | "dry_run" | "enabled";

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
  );
}

function PlusIcon() {
  return (
    <StrokeIcon>
      <path d="M12 5v14" />
      <path d="M5 12h14" />
    </StrokeIcon>
  );
}

function PencilIcon() {
  return (
    <StrokeIcon>
      <path d="M4 20h4l10.5-10.5a2.828 2.828 0 1 0-4-4L4 16v4" />
      <path d="M13.5 6.5l4 4" />
    </StrokeIcon>
  );
}

function HistoryIcon() {
  return (
    <StrokeIcon>
      <path d="M12 8v4l3 3" />
      <path d="M3.05 11a9 9 0 1 1 .5 4" />
      <path d="M3 4v5h5" />
    </StrokeIcon>
  );
}

function ScheduleCell({ job }: { job: Job }) {
  const { preferences } = useDisplayPreferences();
  const cronText = (
    <Text
      size="sm"
      ff="monospace"
      component="span"
      style={{ display: "inline-block", cursor: job.enabled ? "help" : undefined }}
    >
      {job.cron}
    </Text>
  );

  if (!job.enabled) {
    return cronText;
  }

  const label = job.next_run_at
    ? `Next run: ${formatScheduleDateTime(job.next_run_at, preferences)}`
    : "Next run unavailable";

  return (
    <Tooltip label={label} withArrow openDelay={200}>
      {cronText}
    </Tooltip>
  );
}

export function JobsPage() {
  const queryClient = useQueryClient();
  const [sort, setSort] = useState<SortState<JobSortColumn> | null>(null);
  const jobsQuery = useQuery({
    queryKey: ["jobs"],
    queryFn: listJobs,
  });

  const runMutation = useMutation({
    mutationFn: (job: Job) => runJob(job.id),
    onSuccess: (run) => {
      void queryClient.invalidateQueries({ queryKey: ["runs"] });
      notifications.show({
        color: run.status === "success" ? "green" : "orange",
        message: `Run #${run.id} finished with status ${run.status}`,
      });
    },
    onError: (error: unknown) => {
      const message = error instanceof ApiError ? String(error.message) : "Run failed";
      notifications.show({ color: "red", message });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (jobId: number) => deleteJob(jobId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["jobs"] });
      notifications.show({ color: "green", message: "Job deleted" });
    },
    onError: (error: unknown) => {
      const message = error instanceof ApiError ? String(error.message) : "Delete failed";
      notifications.show({ color: "red", message });
    },
  });

  if (jobsQuery.isLoading) {
    return (
      <Group>
        <Loader size="sm" />
        <Text>Loading jobs…</Text>
      </Group>
    );
  }

  if (jobsQuery.isError) {
    return <Text c="red">Could not load jobs.</Text>;
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
  });

  function handleSort(column: JobSortColumn) {
    setSort((current) => nextSortState(current, column));
  }

  return (
    <Stack gap="md">
      <Group justify="space-between">
        <Title order={3}>Sync jobs</Title>
        <Button component={Link} to="/jobs/new" leftSection={<PlusIcon />}>
          New job
        </Button>
      </Group>

      {jobs.length === 0 ? (
        <Text c="dimmed">No jobs yet. Create one to start syncing on a schedule.</Text>
      ) : (
        <Table striped highlightOnHover>
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
              <Table.Tr
                key={job.id}
                className={job.dry_run ? dryRunRowClasses.dryRunRow : undefined}
              >
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
                  <Group gap="xs">
                    <Tooltip label="Run now">
                      <ActionIcon
                        variant="light"
                        aria-label="Run now"
                        loading={runMutation.isPending && runMutation.variables?.id === job.id}
                        onClick={() => runMutation.mutate(job)}
                      >
                        ▶
                      </ActionIcon>
                    </Tooltip>
                    <Button
                      component={Link}
                      to={`/jobs/${job.id}/edit`}
                      size="xs"
                      variant="subtle"
                      leftSection={<PencilIcon />}
                    >
                      Edit
                    </Button>
                    <Button
                      component={Link}
                      to={`/runs?job_id=${job.id}`}
                      size="xs"
                      variant="subtle"
                      leftSection={<HistoryIcon />}
                    >
                      History
                    </Button>
                    <Button
                      size="xs"
                      color="red"
                      variant="subtle"
                      leftSection={<TrashIcon />}
                      loading={deleteMutation.isPending && deleteMutation.variables === job.id}
                      onClick={() => {
                        if (window.confirm(`Delete job "${job.name}"?`)) {
                          deleteMutation.mutate(job.id);
                        }
                      }}
                    >
                      Delete
                    </Button>
                  </Group>
                </Table.Td>
              </Table.Tr>
            ))}
          </Table.Tbody>
        </Table>
      )}
    </Stack>
  );
}
