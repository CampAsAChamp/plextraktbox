import { MantineProvider } from "@mantine/core"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { render, screen, waitFor } from "@testing-library/react"
import { MemoryRouter } from "react-router-dom"
import { afterEach, beforeEach, expect, test, vi } from "vitest"

import { getUnreadCount, isLocalDevApi } from "src/api/notifications"
import { NotificationBell } from "src/components/notifications/NotificationBell"
import { DisplayPreferencesProvider } from "src/settings/DisplayPreferencesProvider"
import { theme } from "src/theme"

vi.mock("src/api/notifications", async (importOriginal) => {
  const mod = await importOriginal<typeof import("src/api/notifications")>()
  return {
    ...mod,
    getUnreadCount: vi.fn(),
    isLocalDevApi: vi.fn(),
  }
})

function renderBell(queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })) {
  render(
    <MantineProvider theme={theme} forceColorScheme="dark">
      <QueryClientProvider client={queryClient}>
        <DisplayPreferencesProvider>
          <MemoryRouter>
            <NotificationBell />
          </MemoryRouter>
        </DisplayPreferencesProvider>
      </QueryClientProvider>
    </MantineProvider>,
  )
  return queryClient
}

function ringingIcon(): Element | null {
  return screen.getByRole("button", { name: /Notifications/i }).querySelector("[class*='ringing']")
}

beforeEach(() => {
  vi.mocked(isLocalDevApi).mockResolvedValue(false)
  window.matchMedia = (query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => undefined,
    removeListener: () => undefined,
    addEventListener: () => undefined,
    removeEventListener: () => undefined,
    dispatchEvent: () => false,
  })
})

afterEach(() => {
  vi.clearAllMocks()
})

test("rings the bell when unread count goes from zero to positive", async () => {
  let unread = 0
  vi.mocked(getUnreadCount).mockImplementation(() => {
    const snapshot = unread
    return Promise.resolve({ unread_count: snapshot })
  })

  const queryClient = renderBell()
  await waitFor(() => {
    expect(queryClient.getQueryData(["notifications", "unread-count"])).toEqual({ unread_count: 0 })
  })
  expect(ringingIcon()).toBeNull()

  unread = 2
  await queryClient.invalidateQueries({ queryKey: ["notifications", "unread-count"] })

  await waitFor(() => {
    expect(ringingIcon()).not.toBeNull()
  })
})

test("does not ring on initial load when unread is already positive", async () => {
  vi.mocked(getUnreadCount).mockResolvedValue({ unread_count: 4 })

  renderBell()
  await screen.findByRole("button", { name: "Notifications, 4 unread" })

  expect(ringingIcon()).toBeNull()
})

test("does not ring when unread increases from a positive count", async () => {
  let unread = 1
  vi.mocked(getUnreadCount).mockImplementation(() => {
    const snapshot = unread
    return Promise.resolve({ unread_count: snapshot })
  })

  const queryClient = renderBell()
  await waitFor(() => {
    expect(queryClient.getQueryData(["notifications", "unread-count"])).toEqual({ unread_count: 1 })
  })

  unread = 3
  await queryClient.invalidateQueries({ queryKey: ["notifications", "unread-count"] })
  await screen.findByRole("button", { name: "Notifications, 3 unread" })

  expect(ringingIcon()).toBeNull()
})
