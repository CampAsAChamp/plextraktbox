import { AppShell, Badge, Group, Text, Title } from "@mantine/core";
import { useQuery } from "@tanstack/react-query";
import { api } from "./api/client";

interface Health {
  status: string;
  version: string;
}

// Phase 0 shell: proves the SPA boots and can reach the API. The auth-gate,
// setup-gate, and router pages are layered in from Phase 1 onward.
export function App() {
  const { data, isError } = useQuery({
    queryKey: ["health"],
    queryFn: () => api.get<Health>("/health"),
  });

  return (
    <AppShell header={{ height: 56 }} padding="md">
      <AppShell.Header>
        <Group h="100%" px="md" justify="space-between">
          <Title order={4}>media-sync</Title>
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
      </AppShell.Header>
      <AppShell.Main>
        <Text>
          Scaffold is running. Plex, Letterboxd, and Trakt sync features are built out phase by phase.
        </Text>
      </AppShell.Main>
    </AppShell>
  );
}
