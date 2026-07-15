import { Alert, Badge, Button, Group, Stack, Text, Title } from "@mantine/core";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import type { User } from "../api/auth";
import type { ConnectionSummary } from "../api/connections";
import { listJobs } from "../api/jobApi";
import { listRuns } from "../api/runs";
import { ConnectionStatusBadge } from "../components/connections/ConnectionStatusBadge";
import { RunStatusBadge } from "../components/runs/RunBadges";

interface DashboardPageProps {
  user: User;
  connections?: ConnectionSummary[];
}

export function DashboardPage({ user, connections = [] }: DashboardPageProps) {
  const jobsQuery = useQuery({
    queryKey: ["jobs"],
    queryFn: listJobs,
  });

  const runsQuery = useQuery({
    queryKey: ["runs", { recent: true }],
    queryFn: () => listRuns({ limit: 5 }),
  });

  const needsReauth = connections.some((item) => item.status === "needs_reauth");
  const jobs = jobsQuery.data ?? [];
  const recentRuns = runsQuery.data?.items ?? [];

  return (
    <Stack gap="md" maw="85%" mx="auto">
      <Title order={3}>Dashboard</Title>
      <Text>
        Signed in as <strong>{user.username}</strong> ({user.email}).
      </Text>

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

      <Group>
        <Badge color="blue" variant="light">
          {jobs.length} job{jobs.length === 1 ? "" : "s"}
        </Badge>
      </Group>

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
          <Text fw={500}>Sync jobs</Text>
          <Button component={Link} to="/jobs" variant="light" size="xs">
            View all
          </Button>
        </Group>
        {jobs.length === 0 ? (
          <Text c="dimmed" size="sm">
            No jobs yet.{" "}
            <Text component={Link} to="/jobs/new" span c="blue">
              Create your first job
            </Text>
            .
          </Text>
        ) : (
          <Text size="sm">
            {jobs.filter((job) => job.enabled).length} enabled ·{" "}
            {jobs.filter((job) => job.dry_run).length} dry-run
          </Text>
        )}
      </Stack>

      <Stack gap="xs">
        <Group justify="space-between">
          <Text fw={500}>Recent runs</Text>
          <Button component={Link} to="/runs" variant="light" size="xs">
            View history
          </Button>
        </Group>
        {recentRuns.length === 0 ? (
          <Text c="dimmed" size="sm">
            No runs yet.
          </Text>
        ) : (
          <Stack gap={4}>
            {recentRuns.map((run) => (
              <Group key={run.id} gap="sm">
                <Button component={Link} to={`/runs/${run.id}`} variant="subtle" size="compact-xs">
                  #{run.id}
                </Button>
                <Text size="sm">{run.job_name ?? `Job #${run.job_id}`}</Text>
                <RunStatusBadge status={run.status} />
              </Group>
            ))}
          </Stack>
        )}
      </Stack>
    </Stack>
  );
}
