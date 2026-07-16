import {
  ActionIcon,
  AppShell,
  Avatar,
  Box,
  Burger,
  Button,
  Drawer,
  Group,
  Menu,
  NavLink,
  Stack,
  Title,
  useMantineTheme,
} from "@mantine/core";
import { useDisclosure } from "@mantine/hooks";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Link, Outlet, useLocation, useNavigate } from "react-router-dom";
import { api } from "src/api/client";
import { formatVersionLabel, useHealthQuery } from "src/api/health";
import { GitHubIcon } from "src/components/icons/GitHubIcon";
import { HomeIcon } from "src/components/icons/HomeIcon";
import { ApiHealthBadge } from "src/components/layout/ApiHealthBadge";
import { NotificationBell } from "src/components/notifications/NotificationBell";

const GITHUB_REPO_URL = "https://github.com/CampAsAChamp/plextraktbox";

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

const NAV_LINKS = [
  { to: "/jobs", label: "Jobs", match: (path: string) => path.startsWith("/jobs") },
  { to: "/runs", label: "Runs", match: (path: string) => path.startsWith("/runs") },
  {
    to: "/connections",
    label: "Connections",
    match: (path: string) => path.startsWith("/connections"),
  },
] as const;

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
  const theme = useMantineTheme();
  const primary = theme.primaryColor;
  const [navOpened, { toggle: toggleNav, close: closeNav }] = useDisclosure(false);
  const isHome = location.pathname === "/";
  const isSettings = location.pathname.startsWith("/settings");
  const showHome = showLogout;
  const queryClient = useQueryClient();
  const { data: health } = useHealthQuery();
  const versionLabel = health ? formatVersionLabel(health) : null;
  const logout = useMutation({
    mutationFn: () => api.post<void>("/auth/logout"),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["auth", "me"] });
      navigate("/login", { replace: true });
    },
  });

  return (
    <AppShell header={{ height: 64 }} padding="md">
      <AppShell.Header>
        <Group h="100%" px="md" justify="space-between" wrap="nowrap">
          <Group gap="sm" wrap="nowrap" style={{ minWidth: 0 }}>
            {showLogout ? (
              <Burger
                opened={navOpened}
                onClick={toggleNav}
                hiddenFrom="sm"
                size="sm"
                aria-label="Open navigation"
              />
            ) : null}
            {showHome ? (
              <Link
                to="/"
                aria-label="Go to dashboard"
                aria-current={isHome ? "page" : undefined}
                style={{
                  color: "inherit",
                  textDecoration: "none",
                  cursor: "pointer",
                  minWidth: 0,
                }}
              >
                <Group gap="sm" wrap="nowrap">
                  <Title
                    order={3}
                    fw={700}
                    style={{ letterSpacing: "-0.02em" }}
                    lineClamp={1}
                  >
                    plextraktbox
                  </Title>
                  <ActionIcon
                    component="span"
                    variant={isHome ? "light" : "subtle"}
                    color={isHome ? primary : "gray"}
                    size="lg"
                    aria-hidden
                    tabIndex={-1}
                    visibleFrom="sm"
                  >
                    <HomeIcon size={18} />
                  </ActionIcon>
                </Group>
              </Link>
            ) : (
              <Title order={3} fw={700} style={{ letterSpacing: "-0.02em" }}>
                plextraktbox
              </Title>
            )}
            {showLogout ? (
              <Group gap={4} visibleFrom="sm">
                {NAV_LINKS.map((link) => {
                  const active = link.match(location.pathname);
                  return (
                    <Button
                      key={link.to}
                      component={Link}
                      to={link.to}
                      variant={active ? "light" : "subtle"}
                      color={active ? primary : "gray"}
                      size="compact-sm"
                      aria-current={active ? "page" : undefined}
                    >
                      {link.label}
                    </Button>
                  );
                })}
              </Group>
            ) : null}
          </Group>
          <Group gap="xs" wrap="nowrap">
            <ApiHealthBadge />
            {showLogout ? <NotificationBell /> : null}
            {showLogout && username ? (
              <Menu position="bottom-end" width={200} withinPortal trigger="click">
                <Menu.Target>
                  <Button
                    variant="subtle"
                    color="gray"
                    size="compact-sm"
                    px="sm"
                    py="xs"
                    h={44}
                    miw={44}
                    leftSection={
                      avatarUrl ? (
                        <Avatar src={avatarUrl} alt="" size={24} radius="xl" />
                      ) : undefined
                    }
                    rightSection={<ChevronDownIcon />}
                    styles={{
                      root: { overflow: "visible" },
                      label: { lineHeight: 1, overflow: "visible" },
                      section: { overflow: "visible" },
                    }}
                    aria-label="Account menu"
                  >
                    <Box component="span" visibleFrom="sm">
                      {username}
                    </Box>
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
                  {versionLabel ? <Menu.Label>{versionLabel}</Menu.Label> : null}
                  <Menu.Item
                    component="a"
                    href={GITHUB_REPO_URL}
                    target="_blank"
                    rel="noopener noreferrer"
                    leftSection={<GitHubIcon />}
                  >
                    GitHub Repo
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

      {showLogout ? (
        <Drawer
          opened={navOpened}
          onClose={closeNav}
          title="Navigation"
          padding="md"
          size="xs"
          hiddenFrom="sm"
          zIndex={300}
        >
          <Stack gap="xs">
            <NavLink
              component={Link}
              to="/"
              label="Dashboard"
              leftSection={<HomeIcon size={18} />}
              active={isHome}
              onClick={closeNav}
            />
            {NAV_LINKS.map((link) => (
              <NavLink
                key={link.to}
                component={Link}
                to={link.to}
                label={link.label}
                active={link.match(location.pathname)}
                onClick={closeNav}
              />
            ))}
            <NavLink
              component={Link}
              to="/settings"
              label="Settings"
              leftSection={<SettingsIcon size={18} />}
              active={isSettings}
              onClick={closeNav}
            />
          </Stack>
        </Drawer>
      ) : null}

      <AppShell.Main>
        <Outlet />
      </AppShell.Main>
    </AppShell>
  );
}
