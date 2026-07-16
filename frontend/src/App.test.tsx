import { screen, waitFor } from "@testing-library/react"
import { afterEach, beforeEach, expect, test, vi } from "vitest"

import { App } from "src/App"
import { renderWithProviders } from "src/test/render"

function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  })
}

beforeEach(() => {
  vi.stubGlobal("fetch", vi.fn())
})

afterEach(() => {
  vi.unstubAllGlobals()
})

test("redirects to setup when no user exists", async () => {
  vi.mocked(fetch)
    .mockResolvedValueOnce(jsonResponse({ needs_setup: true }))
    .mockResolvedValueOnce(jsonResponse({ status: "ok", version: "0.1.0" }))

  renderWithProviders(<App />)

  await waitFor(() => {
    expect(screen.getByText("Welcome to plextraktbox")).toBeInTheDocument()
  })
})

test("shows login when setup is complete and session is absent", async () => {
  vi.mocked(fetch)
    .mockResolvedValueOnce(jsonResponse({ needs_setup: false }))
    .mockResolvedValueOnce(jsonResponse({ detail: "Not authenticated" }, 401))

  renderWithProviders(<App />)

  await waitFor(() => {
    expect(screen.getByRole("heading", { name: "Sign in" })).toBeInTheDocument()
  })
})

function connectionsPending() {
  return jsonResponse({
    needs_connections: true,
    connections: [
      { service: "plex", status: "unconfigured", config: {}, token_expires_at: null },
      { service: "trakt", status: "unconfigured", config: {}, token_expires_at: null },
      { service: "letterboxd", status: "unconfigured", config: {}, token_expires_at: null },
      { service: "tmdb", status: "unconfigured", config: {}, token_expires_at: null },
    ],
  })
}

function connectionsReady() {
  return jsonResponse({
    needs_connections: false,
    connections: [
      {
        service: "plex",
        status: "ok",
        config: { url: "http://plex.local:32400" },
        token_expires_at: null,
      },
      { service: "trakt", status: "ok", config: {}, token_expires_at: null },
      { service: "letterboxd", status: "ok", config: { username: "nick" }, token_expires_at: null },
      { service: "tmdb", status: "ok", config: {}, token_expires_at: null },
    ],
  })
}

const nickUser = {
  id: 1,
  username: "nick",
  email: "nick@example.com",
  avatar_url: "https://www.gravatar.com/avatar/484f70e21a3d3480e013519f8236bb86?s=80&d=identicon",
}

function unreadCount() {
  return jsonResponse({ unread_count: 0 })
}

test("shows dashboard when connections are incomplete", async () => {
  vi.mocked(fetch)
    .mockResolvedValueOnce(jsonResponse({ needs_setup: false }))
    .mockResolvedValueOnce(jsonResponse(nickUser))
    .mockResolvedValueOnce(connectionsPending())
    .mockResolvedValueOnce(jsonResponse({ status: "ok", version: "0.1.0" }))
    .mockResolvedValue(unreadCount())

  renderWithProviders(<App />)

  await waitFor(() => {
    expect(screen.getByRole("heading", { name: "Dashboard" })).toBeInTheDocument()
    expect(screen.getByText("nick")).toBeInTheDocument()
  })
})

test("shows dashboard when setup is complete and session is present", async () => {
  vi.mocked(fetch)
    .mockResolvedValueOnce(jsonResponse({ needs_setup: false }))
    .mockResolvedValueOnce(jsonResponse(nickUser))
    .mockResolvedValueOnce(connectionsReady())
    .mockResolvedValueOnce(jsonResponse({ status: "ok", version: "0.1.0" }))
    .mockResolvedValue(unreadCount())

  renderWithProviders(<App />)

  await waitFor(() => {
    expect(screen.getByRole("heading", { name: "Dashboard" })).toBeInTheDocument()
    expect(screen.getByText("nick")).toBeInTheDocument()
  })
})
