import { ActionIcon, Badge, Button, Group, Indicator, Menu, ScrollArea, Stack, Text } from "@mantine/core"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useEffect, useRef } from "react"
import { Link } from "react-router-dom"

import {
  clearAllInAppNotifications,
  deleteInAppNotification,
  getUnreadCount,
  type InAppNotification,
  listInAppNotifications,
  markAllInAppRead,
  markInAppRead,
} from "src/api/notifications"
import { CheckIcon } from "src/components/icons/CheckIcon"
import { TrashIcon } from "src/components/icons/TrashIcon"
import { useDisplayPreferences } from "src/settings/DisplayPreferencesProvider"
import { showToast } from "src/toast"
import { formatDateTime } from "src/utils/dateTimeFormat"

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
  )
}

function levelColor(level: InAppNotification["level"]) {
  switch (level) {
    case "success":
      return "green"
    case "warning":
      return "yellow"
    case "error":
      return "red"
    default:
      return "blue"
  }
}

function errorMessage(error: unknown, fallback: string): string {
  return error instanceof Error ? error.message : fallback
}

function NotificationItem({
  item,
  onRead,
  onDelete,
  deleting,
}: {
  item: InAppNotification
  onRead: (id: number) => void
  onDelete: (id: number) => void
  deleting: boolean
}) {
  const { preferences } = useDisplayPreferences()

  const deleteButton = (
    <ActionIcon
      size="sm"
      variant="subtle"
      color="gray"
      aria-label="Delete notification"
      loading={deleting}
      onClick={(event) => {
        event.preventDefault()
        event.stopPropagation()
        onDelete(item.id)
      }}
    >
      <TrashIcon size={12} />
    </ActionIcon>
  )

  const content = (
    <Stack gap={2}>
      <Group justify="space-between" wrap="nowrap" gap="xs">
        <Text size="sm" fw={item.read ? 400 : 600} lineClamp={1}>
          {item.title}
        </Text>
        <Group gap={4} wrap="nowrap">
          <Badge size="xs" color={levelColor(item.level)} variant="light">
            {item.level}
          </Badge>
          {deleteButton}
        </Group>
      </Group>
      <Text size="xs" c="dimmed" lineClamp={2}>
        {item.body}
      </Text>
      <Text size="xs" c="dimmed">
        {formatDateTime(item.created_at, preferences)}
      </Text>
    </Stack>
  )

  if (item.run_id != null && item.run_id > 0) {
    return (
      <Menu.Item
        component={Link}
        to={`/runs/${item.run_id}`}
        onClick={() => {
          if (!item.read) onRead(item.id)
        }}
      >
        {content}
      </Menu.Item>
    )
  }

  return <Menu.Item onClick={() => !item.read && onRead(item.id)}>{content}</Menu.Item>
}

export function NotificationBell() {
  const queryClient = useQueryClient()
  const unreadErrorToasted = useRef(false)
  const unreadQuery = useQuery({
    queryKey: ["notifications", "unread-count"],
    queryFn: getUnreadCount,
    refetchInterval: 30_000,
  })
  const listQuery = useQuery({
    queryKey: ["notifications", "inapp"],
    queryFn: () => listInAppNotifications(false),
    enabled: false,
  })

  useEffect(() => {
    if (unreadQuery.isError) {
      if (!unreadErrorToasted.current) {
        unreadErrorToasted.current = true
        showToast({
          color: "red",
          message: errorMessage(unreadQuery.error, "Could not load notification count"),
        })
      }
      return
    }
    unreadErrorToasted.current = false
  }, [unreadQuery.isError, unreadQuery.error])

  const markRead = useMutation({
    mutationFn: markInAppRead,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["notifications"] })
    },
    onError: (error: unknown) => {
      showToast({
        color: "red",
        message: errorMessage(error, "Could not mark notification read"),
      })
    },
  })

  const markAll = useMutation({
    mutationFn: markAllInAppRead,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["notifications"] })
      showToast({ color: "green", message: "All notifications marked read" })
    },
    onError: (error: unknown) => {
      showToast({
        color: "red",
        message: errorMessage(error, "Could not mark notifications read"),
      })
    },
  })

  const remove = useMutation({
    mutationFn: deleteInAppNotification,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["notifications"] })
    },
    onError: (error: unknown) => {
      showToast({
        color: "red",
        message: errorMessage(error, "Could not delete notification"),
      })
    },
  })

  const clearAll = useMutation({
    mutationFn: clearAllInAppNotifications,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["notifications"] })
      showToast({ color: "green", message: "All notifications cleared" })
    },
    onError: (error: unknown) => {
      showToast({
        color: "red",
        message: errorMessage(error, "Could not clear notifications"),
      })
    },
  })

  const unreadCount = unreadQuery.data?.unread_count ?? 0
  const itemCount = listQuery.data?.items.length ?? 0

  return (
    <Menu
      position="bottom-end"
      width="min(360px, calc(100vw - 2rem))"
      withinPortal
      onOpen={() => {
        void listQuery.refetch()
      }}
    >
      <Menu.Target>
        <Indicator inline disabled={unreadCount === 0} color="blue" size={8} offset={4}>
          <ActionIcon variant="subtle" color={unreadCount > 0 ? "blue" : "gray"} size="lg" miw={44} h={44} aria-label="Notifications">
            <BellIcon />
          </ActionIcon>
        </Indicator>
      </Menu.Target>
      <Menu.Dropdown>
        <Group justify="space-between" px="sm" py={4} wrap="nowrap" gap="xs">
          <Menu.Label style={{ padding: 0 }}>Notifications</Menu.Label>
          <Group gap={4} wrap="nowrap">
            <Button
              variant="subtle"
              size="compact-xs"
              disabled={unreadCount === 0 || markAll.isPending}
              leftSection={<CheckIcon size={12} />}
              onClick={() => markAll.mutate()}
            >
              Mark all read
            </Button>
            <Button
              variant="subtle"
              color="red"
              size="compact-xs"
              disabled={itemCount === 0 || clearAll.isPending}
              leftSection={<TrashIcon size={12} />}
              onClick={() => clearAll.mutate()}
            >
              Clear all
            </Button>
          </Group>
        </Group>
        <ScrollArea.Autosize mah={360} type="auto">
          {listQuery.isFetching && !listQuery.data ? (
            <Text size="sm" c="dimmed" px="sm" py="md">
              Loading…
            </Text>
          ) : listQuery.isError ? (
            <Text size="sm" c="red" px="sm" py="md">
              {errorMessage(listQuery.error, "Could not load notifications")}
            </Text>
          ) : listQuery.data?.items.length ? (
            listQuery.data.items.map((item) => (
              <NotificationItem
                key={item.id}
                item={item}
                onRead={(id) => markRead.mutate(id)}
                onDelete={(id) => remove.mutate(id)}
                deleting={remove.isPending && remove.variables === item.id}
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
  )
}
