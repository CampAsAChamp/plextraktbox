import { AppShell, Button, Group, Title } from "@mantine/core";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Outlet, useNavigate } from "react-router-dom";
import { api } from "../../api/client";

interface AppLayoutProps {
  username?: string;
  showLogout?: boolean;
}

export function AppLayout({ username, showLogout = false }: AppLayoutProps) {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const logout = useMutation({
    mutationFn: () => api.post<void>("/auth/logout"),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["auth", "me"] });
      navigate("/login", { replace: true });
    },
  });

  return (
    <AppShell header={{ height: 56 }} padding="md">
      <AppShell.Header>
        <Group h="100%" px="md" justify="space-between">
          <Title order={4}>plextraktbox</Title>
          {showLogout && username ? (
            <Group gap="sm">
              <span>{username}</span>
              <Button
                size="xs"
                variant="light"
                loading={logout.isPending}
                onClick={() => logout.mutate()}
              >
                Log out
              </Button>
            </Group>
          ) : null}
        </Group>
      </AppShell.Header>
      <AppShell.Main>
        <Outlet />
      </AppShell.Main>
    </AppShell>
  );
}
