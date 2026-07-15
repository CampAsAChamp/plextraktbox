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
import { Link } from "react-router-dom";
import type { Job } from "../api/jobs";
import { DataTypeBadge } from "../components/services/DataTypeBadge";
import { SourcePairLabel } from "../components/services/SourcePairLabel";
import { ApiError } from "../api/client";
import { deleteJob, listJobs, runJob } from "../api/jobApi";
import { DryRunBadge, JobStatusBadge } from "../components/JobForm/JobForm";
import { TrashIcon } from "../components/icons/TrashIcon";
import dryRunRowClasses from "../styles/dryRunRow.module.css";

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


export function JobsPage() {
  const queryClient = useQueryClient();
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

  const jobs = jobsQuery.data ?? [];

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
              <Table.Th>Name</Table.Th>
              <Table.Th>Job Type</Table.Th>
              <Table.Th>Data</Table.Th>
              <Table.Th>Schedule</Table.Th>
              <Table.Th>Dry run</Table.Th>
              <Table.Th>Status</Table.Th>
              <Table.Th>Actions</Table.Th>
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {jobs.map((job) => (
              <Table.Tr
                key={job.id}
                className={job.dry_run ? dryRunRowClasses.dryRunRow : undefined}
              >
                <Table.Td>
                  <Text fw={500}>{job.name}</Text>
                </Table.Td>
                <Table.Td>
                  <SourcePairLabel sourcePair={job.source_pair} variant="icons" />
                </Table.Td>
                <Table.Td>
                  <Group gap={4}>
                    {job.data_types.map((dt) => (
                      <DataTypeBadge key={dt} dataType={dt} />
                    ))}
                  </Group>
                </Table.Td>
                <Table.Td>
                  <Text size="sm" ff="monospace">
                    {job.cron}
                  </Text>
                </Table.Td>
                <Table.Td>
                  <DryRunBadge dryRun={job.dry_run} compact />
                </Table.Td>
                <Table.Td>
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
