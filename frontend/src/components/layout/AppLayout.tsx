import { ActionIcon, AppShell, Button, Group, Title, Tooltip } from "@mantine/core";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Link, Outlet, useLocation, useNavigate } from "react-router-dom";
import { api } from "../../api/client";

function HomeIcon({ size = 18 }: { size?: number }) {
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
      <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
      <polyline points="9 22 9 12 15 12 15 22" />
    </svg>
  );
}

interface AppLayoutProps {
  username?: string;
  showLogout?: boolean;
}

export function AppLayout({ username, showLogout = false }: AppLayoutProps) {
  const location = useLocation();
  const navigate = useNavigate();
  const isHome = location.pathname === "/";
  const showHome = showLogout;
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
          <Group gap="sm">
            {showHome ? (
              <Tooltip label="Dashboard">
                {isHome ? (
                  <ActionIcon
                    component="span"
                    variant="light"
                    size="lg"
                    aria-label="Dashboard"
                    aria-current="page"
                  >
                    <HomeIcon />
                  </ActionIcon>
                ) : (
                  <ActionIcon
                    component={Link}
                    to="/"
                    variant="subtle"
                    size="lg"
                    aria-label="Go to dashboard"
                  >
                    <HomeIcon />
                  </ActionIcon>
                )}
              </Tooltip>
            ) : null}
            <Title order={4}>plextraktbox</Title>
          </Group>
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
