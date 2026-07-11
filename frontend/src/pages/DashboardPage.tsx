import { Alert, Badge, Button, Group, Stack, Text, Title } from "@mantine/core";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import type { User } from "../api/auth";
import type { ConnectionSummary } from "../api/connections";
import { ConnectionStatusBadge } from "../components/connections/ConnectionStatusBadge";

interface Health {
  status: string;
  version: string;
}

interface DashboardPageProps {
  user: User;
  connections?: ConnectionSummary[];
}

export function DashboardPage({ user, connections = [] }: DashboardPageProps) {
  const { data, isError } = useQuery({
    queryKey: ["health"],
    queryFn: () => api.get<Health>("/health"),
  });

  const needsReauth = connections.some((item) => item.status === "needs_reauth");

  return (
    <Stack gap="md">
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
        {data ? (
          <Badge color="green" variant="light">
            API ✓ · v{data.version}
          </Badge>
        ) : isError ? (
          <Badge color="red" variant="light">
            API unreachable
          </Badge>
        ) : (
          <Badge color="gray" variant="light">
            connecting…
          </Badge>
        )}
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

      <Text c="dimmed">
        Sync jobs and live logs arrive in Phase 4+. Connections are configured and ready.
      </Text>
    </Stack>
  );
}
