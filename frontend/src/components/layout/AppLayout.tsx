import {
  ActionIcon,
  AppShell,
  Avatar,
  Button,
  Group,
  Menu,
  NavLink,
  Title,
  Tooltip,
} from "@mantine/core";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Link, Outlet, useLocation, useNavigate } from "react-router-dom";
import { api } from "../../api/client";
import { ApiHealthBadge } from "./ApiHealthBadge";

function ChevronDownIcon({ size = 14 }: { size?: number }) {
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
      <polyline points="6 9 12 15 18 9" />
    </svg>
  );
}

function SettingsIcon({ size = 14 }: { size?: number }) {
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
      <path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z" />
      <circle cx="12" cy="12" r="3" />
    </svg>
  );
}

function LogoutIcon({ size = 14 }: { size?: number }) {
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
      <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
      <polyline points="16 17 21 12 16 7" />
      <line x1="21" y1="12" x2="9" y2="12" />
    </svg>
  );
}

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
  avatarUrl?: string;
  showLogout?: boolean;
}

export function AppLayout({
  username,
  avatarUrl,
  showLogout = false,
}: AppLayoutProps) {
  const location = useLocation();
  const navigate = useNavigate();
  const isHome = location.pathname === "/";
  const isJobs = location.pathname.startsWith("/jobs");
  const isRuns = location.pathname.startsWith("/runs");
  const isConnections = location.pathname.startsWith("/connections");
  const isSettings = location.pathname.startsWith("/settings");
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
            {showLogout ? (
              <Group gap="xs">
                <NavLink
                  component={Link}
                  to="/jobs"
                  label="Jobs"
                  active={isJobs}
                  variant="subtle"
                  style={{ width: "auto", borderRadius: 4 }}
                />
                <NavLink
                  component={Link}
                  to="/runs"
                  label="Runs"
                  active={isRuns}
                  variant="subtle"
                  style={{ width: "auto", borderRadius: 4 }}
                />
                <NavLink
                  component={Link}
                  to="/connections"
                  label="Connections"
                  active={isConnections}
                  variant="subtle"
                  style={{ width: "auto", borderRadius: 4 }}
                />
              </Group>
            ) : null}
          </Group>
          <Group gap="sm">
            <ApiHealthBadge />
            {showLogout && username ? (
              <Menu
                position="bottom-end"
                width={200}
                withinPortal
                trigger="click-hover"
                openDelay={100}
                closeDelay={400}
              >
                <Menu.Target>
                  <Button
                    variant="subtle"
                    size="compact-sm"
                    px="sm"
                    py="xs"
                    h="auto"
                    styles={{ label: { lineHeight: 1 } }}
                    aria-label="Account menu"
                  >
                    <Group gap={6} wrap="nowrap" align="center">
                      {avatarUrl ? (
                        <Avatar src={avatarUrl} alt="" size={24} radius="xl" />
                      ) : null}
                      <span>{username}</span>
                      <ChevronDownIcon />
                    </Group>
                  </Button>
                </Menu.Target>
                <Menu.Dropdown>
                  <Menu.Label>{username}</Menu.Label>
                  <Menu.Item
                    component={Link}
                    to="/settings"
                    leftSection={<SettingsIcon />}
                    fw={isSettings ? 600 : undefined}
                  >
                    Settings
                  </Menu.Item>
                  <Menu.Divider />
                  <Menu.Item
                    color="red"
                    leftSection={<LogoutIcon />}
                    disabled={logout.isPending}
                    onClick={() => logout.mutate()}
                  >
                    Log out
                  </Menu.Item>
                </Menu.Dropdown>
              </Menu>
            ) : null}
          </Group>
        </Group>
      </AppShell.Header>
      <AppShell.Main>
        <Outlet />
      </AppShell.Main>
    </AppShell>
  );
}
