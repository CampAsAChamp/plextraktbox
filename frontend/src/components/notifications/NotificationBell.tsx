import { ActionIcon, Badge, Button, Group, Indicator, Menu, ScrollArea, Stack, Text } from "@mantine/core"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { type CSSProperties, useEffect, useRef, useState } from "react"
import { Link } from "react-router-dom"

import {
  clearAllInAppNotifications,
  deleteInAppNotification,
  getUnreadCount,
  type InAppListResponse,
  type InAppNotification,
  isLocalDevApi,
  listInAppNotifications,
  markAllInAppRead,
  markInAppRead,
  seedDevInAppNotifications,
} from "src/api/notifications"
import { CheckIcon } from "src/components/icons/CheckIcon"
import { PlusIcon } from "src/components/icons/PlusIcon"
import { TrashIcon } from "src/components/icons/TrashIcon"
import classes from "src/components/notifications/NotificationBell.module.css"
import { TimestampLabel } from "src/components/TimestampLabel"
import { showToast } from "src/toast"

const SWIPE_DURATION_MS = 280
const SWIPE_STAGGER_MS = 55

function BellIcon({ size = 18, filled = false }: { size?: number; filled?: boolean }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill={filled ? "currentColor" : "none"}
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden
    >
      <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
      <path d="M13.73 21a2 2 0 0 1-3.46 0" fill="none" />
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

function prefersReducedMotion(): boolean {
  return typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches
}

function swipeDurationMs(): number {
  return prefersReducedMotion() ? 1 : SWIPE_DURATION_MS
}

/** Bottom item starts first; delay increases toward the top. */
function swipeDelayMs(index: number, count: number): number {
  if (prefersReducedMotion()) return 0
  return Math.max(0, count - 1 - index) * SWIPE_STAGGER_MS
}

function clearAllSwipeMs(count: number): number {
  return swipeDurationMs() + swipeDelayMs(0, count)
}

const EMPTY_REVEAL_MS = 240

function emptyRevealDelayMs(count: number): number {
  if (prefersReducedMotion()) return 0
  return Math.max(80, Math.floor(clearAllSwipeMs(count) * 0.35))
}

function emptyRevealTotalMs(count: number): number {
  if (prefersReducedMotion()) return 1
  return emptyRevealDelayMs(count) + EMPTY_REVEAL_MS
}

function NotificationItem({
  item,
  onRead,
  onDelete,
  swiping,
  swipeDelay,
  dimming,
  dimDelay,
}: {
  item: InAppNotification
  onRead: (id: number) => void
  onDelete: (id: number) => void
  swiping: boolean
  swipeDelay: number
  dimming: boolean
  dimDelay: number
}) {
  const busy = swiping || dimming

  const deleteButton = (
    <ActionIcon
      size="sm"
      variant="subtle"
      color="gray"
      aria-label="Delete notification"
      disabled={busy}
      onClick={(event) => {
        event.preventDefault()
        event.stopPropagation()
        onDelete(item.id)
      }}
    >
      <TrashIcon size={12} />
    </ActionIcon>
  )

  const markReadButton = !item.read ? (
    <ActionIcon
      size="sm"
      variant="subtle"
      color="gray"
      aria-label="Mark notification as read"
      disabled={busy}
      onClick={(event) => {
        event.preventDefault()
        event.stopPropagation()
        onRead(item.id)
      }}
    >
      <CheckIcon size={12} />
    </ActionIcon>
  ) : null

  const content = (
    <Stack gap={2}>
      <Group justify="space-between" wrap="nowrap" gap="xs" align="flex-start">
        <Group gap={6} wrap="nowrap" align="flex-start" style={{ minWidth: 0, flex: 1 }}>
          <Badge size="xs" color={levelColor(item.level)} variant="light" mt={2} style={{ flexShrink: 0 }}>
            {item.level}
          </Badge>
          <Text size="sm" fw={item.read ? 400 : 600} c={item.read ? "dimmed" : undefined} lineClamp={1} style={{ minWidth: 0 }}>
            {item.title}
          </Text>
        </Group>
        <Group gap={2} wrap="nowrap" style={{ flexShrink: 0 }}>
          {markReadButton}
          {deleteButton}
        </Group>
      </Group>
      <Text size="xs" c="dimmed" lineClamp={2}>
        {item.body}
      </Text>
      <TimestampLabel value={item.created_at} size="xs" />
    </Stack>
  )

  const menuItem =
    item.run_id != null && item.run_id > 0 ? (
      <Menu.Item
        component={Link}
        to={`/runs/${item.run_id}`}
        onClick={() => {
          if (!item.read) onRead(item.id)
        }}
      >
        {content}
      </Menu.Item>
    ) : (
      <Menu.Item onClick={() => !item.read && onRead(item.id)}>{content}</Menu.Item>
    )

  const rowClass = [classes.row, item.read && !dimming ? classes.read : "", swiping ? classes.swiping : "", dimming ? classes.dimming : ""]
    .filter(Boolean)
    .join(" ")

  const rowStyle = swiping
    ? ({ "--swipe-delay": `${swipeDelay}ms` } as CSSProperties)
    : dimming
      ? ({ "--dim-delay": `${dimDelay}ms` } as CSSProperties)
      : undefined

  return (
    <div className={rowClass} style={rowStyle}>
      {menuItem}
    </div>
  )
}

export function NotificationBell() {
  const queryClient = useQueryClient()
  const unreadErrorToasted = useRef(false)
  const swipeTimeouts = useRef<number[]>([])
  const [exitingIds, setExitingIds] = useState<Set<number>>(() => new Set())
  const [dimmingIds, setDimmingIds] = useState<Set<number>>(() => new Set())
  const [clearingAll, setClearingAll] = useState(false)
  const [markingAll, setMarkingAll] = useState(false)

  const localDevQuery = useQuery({
    queryKey: ["dev", "local"],
    queryFn: isLocalDevApi,
    staleTime: Infinity,
    retry: false,
  })

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

  useEffect(() => {
    return () => {
      for (const id of swipeTimeouts.current) window.clearTimeout(id)
    }
  }, [])

  const markRead = useMutation({
    mutationFn: markInAppRead,
    onMutate: async (id) => {
      await queryClient.cancelQueries({ queryKey: ["notifications"] })
      const prevList = queryClient.getQueryData<InAppListResponse>(["notifications", "inapp"])
      const prevUnread = queryClient.getQueryData<{ unread_count: number }>(["notifications", "unread-count"])
      queryClient.setQueryData<InAppListResponse>(["notifications", "inapp"], (prev) => {
        if (!prev) return prev
        return {
          ...prev,
          items: prev.items.map((item) => (item.id === id && !item.read ? { ...item, read: true } : item)),
        }
      })
      if (prevUnread && prevUnread.unread_count > 0) {
        const wasUnread = prevList?.items.some((item) => item.id === id && !item.read)
        if (wasUnread) {
          queryClient.setQueryData(["notifications", "unread-count"], {
            unread_count: prevUnread.unread_count - 1,
          })
        }
      }
      setDimmingIds((prev) => {
        if (!prev.has(id)) return prev
        const next = new Set(prev)
        next.delete(id)
        return next
      })
      return { prevList, prevUnread }
    },
    onError: (error: unknown, id, context) => {
      if (context?.prevList) queryClient.setQueryData(["notifications", "inapp"], context.prevList)
      if (context?.prevUnread) queryClient.setQueryData(["notifications", "unread-count"], context.prevUnread)
      setDimmingIds((prev) => {
        if (!prev.has(id)) return prev
        const next = new Set(prev)
        next.delete(id)
        return next
      })
      showToast({
        color: "red",
        message: errorMessage(error, "Could not mark notification read"),
      })
    },
    onSettled: () => {
      void queryClient.invalidateQueries({ queryKey: ["notifications"] })
      void listQuery.refetch()
    },
  })

  const markAll = useMutation({
    mutationFn: markAllInAppRead,
    onMutate: async () => {
      await queryClient.cancelQueries({ queryKey: ["notifications"] })
      const prevList = queryClient.getQueryData<InAppListResponse>(["notifications", "inapp"])
      const prevUnread = queryClient.getQueryData<{ unread_count: number }>(["notifications", "unread-count"])
      queryClient.setQueryData<InAppListResponse>(["notifications", "inapp"], (prev) => {
        if (!prev) return prev
        return { ...prev, items: prev.items.map((item) => (item.read ? item : { ...item, read: true })) }
      })
      queryClient.setQueryData(["notifications", "unread-count"], { unread_count: 0 })
      setDimmingIds(new Set())
      setMarkingAll(false)
      return { prevList, prevUnread }
    },
    onError: (error: unknown, _vars, context) => {
      if (context?.prevList) queryClient.setQueryData(["notifications", "inapp"], context.prevList)
      if (context?.prevUnread) queryClient.setQueryData(["notifications", "unread-count"], context.prevUnread)
      setDimmingIds(new Set())
      setMarkingAll(false)
      showToast({
        color: "red",
        message: errorMessage(error, "Could not mark notifications read"),
      })
    },
    onSettled: () => {
      void queryClient.invalidateQueries({ queryKey: ["notifications"] })
      void listQuery.refetch()
    },
  })

  const remove = useMutation({
    mutationFn: deleteInAppNotification,
    onSuccess: (_data, id) => {
      queryClient.setQueryData<InAppListResponse>(["notifications", "inapp"], (prev) => {
        if (!prev) return prev
        return { ...prev, items: prev.items.filter((item) => item.id !== id) }
      })
      void queryClient.invalidateQueries({ queryKey: ["notifications"] })
      setExitingIds((prev) => {
        if (!prev.has(id)) return prev
        const next = new Set(prev)
        next.delete(id)
        return next
      })
    },
    onError: (error: unknown, id) => {
      setExitingIds((prev) => {
        if (!prev.has(id)) return prev
        const next = new Set(prev)
        next.delete(id)
        return next
      })
      showToast({
        color: "red",
        message: errorMessage(error, "Could not delete notification"),
      })
    },
  })

  const clearAll = useMutation({
    mutationFn: clearAllInAppNotifications,
    onSuccess: () => {
      queryClient.setQueryData<InAppListResponse>(["notifications", "inapp"], (prev) => (prev ? { ...prev, items: [] } : prev))
      void queryClient.invalidateQueries({ queryKey: ["notifications"] })
      setExitingIds(new Set())
      setClearingAll(false)
    },
    onError: (error: unknown) => {
      setExitingIds(new Set())
      setClearingAll(false)
      showToast({
        color: "red",
        message: errorMessage(error, "Could not clear notifications"),
      })
    },
  })

  const seedDev = useMutation({
    mutationFn: seedDevInAppNotifications,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["notifications"] })
      void listQuery.refetch()
      showToast({ color: "green", message: "Added sample notifications" })
    },
    onError: (error: unknown) => {
      showToast({
        color: "red",
        message: errorMessage(error, "Could not seed notifications"),
      })
    },
  })

  const items = listQuery.data?.items ?? []
  const unreadCount = unreadQuery.data?.unread_count ?? 0
  const itemCount = items.length
  const unreadItems = items.filter((item) => !item.read)
  const animating = clearingAll || markingAll || exitingIds.size > 0 || dimmingIds.size > 0
  const allExiting = itemCount > 0 && items.every((item) => exitingIds.has(item.id))
  const revealingEmpty = clearingAll || allExiting
  const showEmpty = itemCount === 0 || revealingEmpty
  const showDevSeed = localDevQuery.data === true
  const emptyDelayMs = revealingEmpty ? emptyRevealDelayMs(itemCount || exitingIds.size) : 0
  const markAllDisabled = unreadCount === 0 || markAll.isPending || markingAll || clearingAll || exitingIds.size > 0
  const clearAllDisabled = itemCount === 0 || clearAll.isPending || clearingAll || exitingIds.size > 0
  const clearAllLocked = markingAll || dimmingIds.size > 0

  function scheduleSwipe(callback: () => void, delayMs: number) {
    const timeoutId = window.setTimeout(() => {
      swipeTimeouts.current = swipeTimeouts.current.filter((id) => id !== timeoutId)
      callback()
    }, delayMs)
    swipeTimeouts.current.push(timeoutId)
  }

  function handleDelete(id: number) {
    if (clearingAll || markingAll || exitingIds.has(id) || dimmingIds.has(id)) return
    setExitingIds((prev) => new Set(prev).add(id))
    const waitMs = itemCount === 1 ? Math.max(swipeDurationMs(), emptyRevealTotalMs(1)) : swipeDurationMs()
    scheduleSwipe(() => remove.mutate(id), waitMs)
  }

  function handleMarkRead(id: number) {
    if (clearingAll || markingAll || exitingIds.has(id) || dimmingIds.has(id)) return
    const item = items.find((entry) => entry.id === id)
    if (!item || item.read) return
    setDimmingIds((prev) => new Set(prev).add(id))
    scheduleSwipe(() => markRead.mutate(id), swipeDurationMs())
  }

  function handleMarkAll() {
    if (unreadItems.length === 0 || markingAll || clearingAll || markAll.isPending) return
    const count = unreadItems.length
    setMarkingAll(true)
    setDimmingIds(new Set(unreadItems.map((item) => item.id)))
    scheduleSwipe(() => markAll.mutate(), clearAllSwipeMs(count))
  }

  function handleClearAll() {
    if (itemCount === 0 || clearingAll || markingAll || clearAll.isPending) return
    const count = itemCount
    setClearingAll(true)
    setExitingIds(new Set(items.map((item) => item.id)))
    scheduleSwipe(() => clearAll.mutate(), Math.max(clearAllSwipeMs(count), emptyRevealTotalMs(count)))
  }

  return (
    <Menu
      position="bottom-end"
      width="min(360px, calc(100vw - 2rem))"
      withinPortal
      styles={{ item: { borderRadius: "var(--mantine-radius-md)" } }}
      onOpen={() => {
        void listQuery.refetch()
      }}
    >
      <Menu.Target>
        <ActionIcon
          variant="subtle"
          color={unreadCount > 0 ? "blue" : "gray"}
          size="lg"
          miw={44}
          h={44}
          aria-label={unreadCount > 0 ? `Notifications, ${unreadCount} unread` : "Notifications"}
        >
          <Indicator inline disabled={unreadCount === 0} color="blue" size={16} offset={2} label={unreadCount > 99 ? "99+" : unreadCount}>
            <BellIcon filled={unreadCount > 0} />
          </Indicator>
        </ActionIcon>
      </Menu.Target>
      <Menu.Dropdown>
        <Group justify="space-between" px="sm" py={4} wrap="nowrap" gap="xs">
          <Menu.Label style={{ padding: 0 }}>Notifications</Menu.Label>
          <Group gap={4} wrap="nowrap">
            <Button
              variant="subtle"
              size="compact-xs"
              className={classes.headerAction}
              disabled={markAllDisabled}
              leftSection={<CheckIcon size={12} />}
              onClick={() => handleMarkAll()}
            >
              Mark all read
            </Button>
            <Button
              variant="subtle"
              color="red"
              size="compact-xs"
              className={classes.headerAction}
              disabled={clearAllDisabled}
              style={clearAllLocked ? { pointerEvents: "none" } : undefined}
              aria-disabled={clearAllDisabled || clearAllLocked}
              leftSection={<TrashIcon size={12} />}
              onClick={() => handleClearAll()}
            >
              Clear all
            </Button>
          </Group>
        </Group>
        <ScrollArea.Autosize mah={360} type="auto" styles={{ viewport: { overflowX: "hidden" } }}>
          {listQuery.isFetching && !listQuery.data ? (
            <Text size="sm" c="dimmed" px="sm" py="md">
              Loading…
            </Text>
          ) : listQuery.isError ? (
            <Text size="sm" c="red" px="sm" py="md">
              {errorMessage(listQuery.error, "Could not load notifications")}
            </Text>
          ) : (
            <div className={classes.listBody}>
              {itemCount > 0 ? (
                <div className={classes.listLayer}>
                  {items.map((item, index) => {
                    const swiping = exitingIds.has(item.id)
                    const dimming = dimmingIds.has(item.id)
                    const unreadIndex = unreadItems.findIndex((unread) => unread.id === item.id)
                    return (
                      <NotificationItem
                        key={item.id}
                        item={item}
                        onRead={handleMarkRead}
                        onDelete={handleDelete}
                        swiping={swiping}
                        swipeDelay={clearingAll ? swipeDelayMs(index, items.length) : 0}
                        dimming={dimming}
                        dimDelay={markingAll && unreadIndex >= 0 ? swipeDelayMs(unreadIndex, unreadItems.length) : 0}
                      />
                    )
                  })}
                </div>
              ) : null}
              {showEmpty ? (
                <Text
                  size="sm"
                  c="dimmed"
                  className={[classes.empty, revealingEmpty ? classes.emptyReveal : ""].filter(Boolean).join(" ")}
                  style={revealingEmpty ? ({ "--empty-delay": `${emptyDelayMs}ms` } as CSSProperties) : undefined}
                >
                  No notifications yet
                </Text>
              ) : null}
            </div>
          )}
        </ScrollArea.Autosize>
        {showDevSeed ? (
          <>
            <Menu.Divider />
            <Stack gap={2} align="center" px="sm" py={6}>
              <Button
                variant="light"
                color="gray"
                size="compact-xs"
                disabled={seedDev.isPending || animating}
                leftSection={<PlusIcon size={12} />}
                onClick={() => seedDev.mutate()}
              >
                Add test notifications
              </Button>
              <Text size="xs" c="dimmed">
                Local only — hidden in production
              </Text>
            </Stack>
          </>
        ) : null}
      </Menu.Dropdown>
    </Menu>
  )
}
