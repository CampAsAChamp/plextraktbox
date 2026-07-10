import { Badge, Group, Stack, Text, Title } from "@mantine/core";
import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import type { User } from "../api/auth";

interface Health {
  status: string;
  version: string;
}

interface DashboardPageProps {
  user: User;
}

export function DashboardPage({ user }: DashboardPageProps) {
  const { data, isError } = useQuery({
    queryKey: ["health"],
    queryFn: () => api.get<Health>("/health"),
  });

  return (
    <Stack gap="md">
      <Title order={3}>Dashboard</Title>
      <Text>
        Signed in as <strong>{user.username}</strong> ({user.email}).
      </Text>
      <Group>
        {data ? (
          <Badge color="green" variant="light">
            API ok · v{data.version}
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
      <Text c="dimmed">
        Connection setup, sync jobs, and live logs arrive in later phases. Phase 1 auth is complete.
      </Text>
    </Stack>
  );
}
