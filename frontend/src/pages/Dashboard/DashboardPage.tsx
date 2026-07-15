import {
  ActionIcon,
  Alert,
  Badge,
  Button,
  Group,
  Loader,
  Stack,
  Table,
  Text,
  Title,
  Tooltip,
} from "@mantine/core";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link } from "react-router-dom";
import type { User } from "../../api/auth";
import type { ConnectionSummary } from "../../api/connections";
import { ApiError } from "../../api/client";
import type { Job } from "../../api/jobs";
import { listJobs, runJob } from "../../api/jobApi";
import { ConnectionStatusBadge } from "../../components/connections/ConnectionStatusBadge";
import { JobStatusBadge } from "../../components/JobForm/JobForm";
import { DryRunBadge, RunStatusBadge } from "../../components/runs/RunBadges";
import { SourcePairLabel } from "../../components/services/SourcePairLabel";
import { RoundedTable } from "../../components/table/RoundedTable";
import { useDisplayPreferences } from "../../settings/DisplayPreferencesProvider";
import { showToast } from "../../toast";
import { formatDateTime, formatScheduleDateTime } from "../../utils/dateTimeFormat";
import dryRunRowClasses from "../../styles/dryRunRow.module.css";

interface DashboardPageProps {
  user: User;
  connections?: ConnectionSummary[];
}

type RunMode = "run" | "dry-run";

/** Stable key for the current set of failed/partial last runs. */
function problemJobsSignature(jobs: Job[]): string {
  return jobs
    .map((job) => `${job.id}:${job.last_run?.id ?? 0}:${job.last_run?.status ?? ""}`)
    .sort()
    .join("|");
}

function nextRunLabel(job: Job, formatNext: (iso: string) => string): string {
  if (!job.enabled) return "Disabled";
  if (!job.next_run_at) return "Unscheduled";
  return formatNext(job.next_run_at);
}

function LastRunCell({ job }: { job: Job }) {
  const { preferences } = useDisplayPreferences();
  const last = job.last_run;
  if (!last) {
    return (
      <Text size="sm" c="dimmed">
        Never run
      </Text>
    );
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
      <Text size="xs">
        matched {last.matched} · added {last.added} · errors {last.errors}
      </Text>
    </Stack>
  );
}

export function DashboardPage({ user, connections = [] }: DashboardPageProps) {
  const queryClient = useQueryClient();
  const { preferences } = useDisplayPreferences();
  const [dismissedProblemsKey, setDismissedProblemsKey] = useState<string | null>(null);

  const jobsQuery = useQuery({
    queryKey: ["jobs"],
    queryFn: listJobs,
  });

  const runMutation = useMutation({
    mutationFn: ({ job, mode }: { job: Job; mode: RunMode }) =>
      runJob(job.id, mode === "dry-run" ? true : undefined),
    onSuccess: (run) => {
      void queryClient.invalidateQueries({ queryKey: ["jobs"] });
      void queryClient.invalidateQueries({ queryKey: ["runs"] });
      showToast({
        color: run.status === "success" ? "green" : "orange",
        message: `Run #${run.id} finished with status ${run.status}`,
      });
    },
    onError: (error: unknown) => {
      const message = error instanceof ApiError ? String(error.message) : "Run failed";
      showToast({ color: "red", message });
    },
  });

  const needsReauth = connections.some((item) => item.status === "needs_reauth");
  const jobs = jobsQuery.data ?? [];
  const problemJobs = jobs.filter(
    (job) => job.last_run?.status === "failed" || job.last_run?.status === "partial",
  );
  const problemsKey = problemJobsSignature(problemJobs);
  const showProblemsAlert =
    problemJobs.length > 0 && problemsKey !== "" && problemsKey !== dismissedProblemsKey;

  function isRunning(job: Job, mode: RunMode): boolean {
    return (
      runMutation.isPending &&
      runMutation.variables?.job.id === job.id &&
      runMutation.variables.mode === mode
    );
  }

  return (
    <Stack gap="md" maw="85%" mx="auto">
      <Group justify="space-between" align="flex-start">
        <Stack gap={4}>
          <Title order={3}>Dashboard</Title>
          <Text size="sm" c="dimmed">
            Signed in as <strong>{user.username}</strong> · job health at a glance
          </Text>
        </Stack>
        <Button component={Link} to="/jobs/new" variant="light" size="sm">
          New job
        </Button>
      </Group>

      {needsReauth ? (
        <Alert color="orange" title="Re-authorization required">
          <Stack gap="xs">
            <Text size="sm">
              One or more service connections need attention. Update credentials to resume sync jobs.
            </Text>
            <Button component={Link} to="/connections" variant="light" size="xs" w="fit-content">
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
          <Stack gap={4}>
            {problemJobs.map((job) => (
              <Group key={job.id} gap="sm">
                <Text size="sm" fw={500}>
                  {job.name}
                </Text>
                {job.last_run ? (
                  <>
                    <RunStatusBadge status={job.last_run.status} />
                    <Button
                      component={Link}
                      to={`/runs/${job.last_run.id}`}
                      variant="subtle"
                      size="compact-xs"
                    >
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
        <Group gap="xs">
          {connections.map((item) => (
            <ConnectionStatusBadge key={item.service} connection={item} />
          ))}
        </Group>
        <Button component={Link} to="/connections" variant="subtle" size="xs" w="fit-content">
          Manage connections
        </Button>
      </Stack>

      <Stack gap="xs">
        <Group justify="space-between">
          <Group gap="sm">
            <Text fw={500}>Jobs</Text>
            <Badge color="blue" variant="light">
              {jobs.length}
            </Badge>
          </Group>
          <Button component={Link} to="/jobs" variant="light" size="xs">
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
          <RoundedTable striped highlightOnHover>
            <Table.Thead>
              <Table.Tr>
                <Table.Th>Job</Table.Th>
                <Table.Th>Next run</Table.Th>
                <Table.Th>Last run</Table.Th>
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
                    <Stack gap={4}>
                      <Group gap="xs">
                        <Text fw={500}>{job.name}</Text>
                        <JobStatusBadge enabled={job.enabled} />
                        <DryRunBadge dryRun={job.dry_run} compact />
                      </Group>
                      <SourcePairLabel sourcePair={job.source_pair} variant="icons" />
                    </Stack>
                  </Table.Td>
                  <Table.Td>
                    <Text size="sm">
                      {nextRunLabel(job, (iso) => formatScheduleDateTime(iso, preferences))}
                    </Text>
                    <Text size="xs" c="dimmed" ff="monospace">
                      {job.cron}
                    </Text>
                  </Table.Td>
                  <Table.Td>
                    <LastRunCell job={job} />
                  </Table.Td>
                  <Table.Td>
                    <Group gap="xs">
                      <Tooltip label="Run now">
                        <ActionIcon
                          variant="light"
                          aria-label={`Run ${job.name}`}
                          loading={isRunning(job, "run")}
                          onClick={() => runMutation.mutate({ job, mode: "run" })}
                        >
                          ▶
                        </ActionIcon>
                      </Tooltip>
                      <Tooltip label="Dry-run">
                        <ActionIcon
                          variant="light"
                          color="blue"
                          aria-label={`Dry-run ${job.name}`}
                          loading={isRunning(job, "dry-run")}
                          onClick={() => runMutation.mutate({ job, mode: "dry-run" })}
                        >
                          ▷
                        </ActionIcon>
                      </Tooltip>
                      <Tooltip label="Edit">
                        <ActionIcon
                          component={Link}
                          to={`/jobs/${job.id}/edit`}
                          variant="subtle"
                          aria-label={`Edit ${job.name}`}
                        >
                          ✎
                        </ActionIcon>
                      </Tooltip>
                    </Group>
                  </Table.Td>
                </Table.Tr>
              ))}
            </Table.Tbody>
          </RoundedTable>
        )}
      </Stack>
    </Stack>
  );
}
