import {
  ActionIcon,
  Badge,
  Button,
  Group,
  Indicator,
  Menu,
  ScrollArea,
  Stack,
  Text,
} from "@mantine/core";
import { showToast } from "../../toast";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import {
  getUnreadCount,
  listInAppNotifications,
  markAllInAppRead,
  markInAppRead,
  type InAppNotification,
} from "../../api/notifications";
import { useDisplayPreferences } from "../../settings/DisplayPreferencesProvider";
import { formatDateTime } from "../../utils/dateTimeFormat";

function BellIcon({ size = 18 }: { size?: number }) {
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
      <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
      <path d="M13.73 21a2 2 0 0 1-3.46 0" />
    </svg>
  );
}

function levelColor(level: InAppNotification["level"]) {
  switch (level) {
    case "success":
      return "green";
    case "warning":
      return "yellow";
    case "error":
      return "red";
    default:
      return "blue";
  }
}

function NotificationItem({
  item,
  onRead,
}: {
  item: InAppNotification;
  onRead: (id: number) => void;
}) {
  const { preferences } = useDisplayPreferences();
  const content = (
    <Stack gap={2}>
      <Group justify="space-between" wrap="nowrap" gap="xs">
        <Text size="sm" fw={item.read ? 400 : 600} lineClamp={1}>
          {item.title}
        </Text>
        <Badge size="xs" color={levelColor(item.level)} variant="light">
          {item.level}
        </Badge>
      </Group>
      <Text size="xs" c="dimmed" lineClamp={2}>
        {item.body}
      </Text>
      <Text size="xs" c="dimmed">
        {formatDateTime(item.created_at, preferences)}
      </Text>
    </Stack>
  );

  if (item.run_id != null && item.run_id > 0) {
    return (
      <Menu.Item
        component={Link}
        to={`/runs/${item.run_id}`}
        onClick={() => {
          if (!item.read) onRead(item.id);
        }}
      >
        {content}
      </Menu.Item>
    );
  }

  return (
    <Menu.Item onClick={() => !item.read && onRead(item.id)}>
      {content}
    </Menu.Item>
  );
}

export function NotificationBell() {
  const queryClient = useQueryClient();
  const unreadQuery = useQuery({
    queryKey: ["notifications", "unread-count"],
    queryFn: getUnreadCount,
    refetchInterval: 30_000,
  });
  const listQuery = useQuery({
    queryKey: ["notifications", "inapp"],
    queryFn: () => listInAppNotifications(false),
    enabled: false,
  });

  const markRead = useMutation({
    mutationFn: markInAppRead,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["notifications"] });
    },
  });

  const markAll = useMutation({
    mutationFn: markAllInAppRead,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["notifications"] });
      showToast({ color: "green", message: "All notifications marked read" });
    },
  });

  const unreadCount = unreadQuery.data?.unread_count ?? 0;

  return (
    <Menu
      position="bottom-end"
      width={360}
      withinPortal
      onOpen={() => {
        void listQuery.refetch();
      }}
    >
      <Menu.Target>
        <Indicator
          inline
          disabled={unreadCount === 0}
          color="blue"
          size={8}
          offset={4}
        >
          <ActionIcon
            variant="subtle"
            color={unreadCount > 0 ? "blue" : "gray"}
            size="lg"
            aria-label="Notifications"
          >
            <BellIcon />
          </ActionIcon>
        </Indicator>
      </Menu.Target>
      <Menu.Dropdown>
        <Group justify="space-between" px="sm" py={4}>
          <Menu.Label style={{ padding: 0 }}>Notifications</Menu.Label>
          <Button
            variant="subtle"
            size="compact-xs"
            disabled={unreadCount === 0 || markAll.isPending}
            onClick={() => markAll.mutate()}
          >
            Mark all read
          </Button>
        </Group>
        <ScrollArea.Autosize mah={360} type="auto">
          {listQuery.isFetching && !listQuery.data ? (
            <Text size="sm" c="dimmed" px="sm" py="md">
              Loading…
            </Text>
          ) : listQuery.data?.items.length ? (
            listQuery.data.items.map((item) => (
              <NotificationItem
                key={item.id}
                item={item}
                onRead={(id) => markRead.mutate(id)}
              />
            ))
          ) : (
            <Text size="sm" c="dimmed" px="sm" py="md">
              No notifications yet
            </Text>
          )}
        </ScrollArea.Autosize>
      </Menu.Dropdown>
    </Menu>
  );
}
