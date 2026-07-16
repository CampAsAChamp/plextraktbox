import { screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import { LoginPage } from "src/pages/LoginPage"
import { renderWithProviders } from "src/test/render"
import * as toast from "src/toast"

function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  })
}

beforeEach(() => {
  vi.stubGlobal("fetch", vi.fn())
  vi.spyOn(toast, "showToast").mockImplementation(() => undefined)
})

afterEach(() => {
  vi.unstubAllGlobals()
  vi.restoreAllMocks()
})

describe("LoginPage", () => {
  it("shows an error when login succeeds but the session cookie does not stick", async () => {
    const user = userEvent.setup()
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse({ id: 1, username: "admin", email: "a@b.c", avatar_url: null }))
      .mockResolvedValueOnce(jsonResponse({ detail: "Not authenticated" }, 401))

    renderWithProviders(<LoginPage />)

    await user.type(screen.getByLabelText(/username or email/i), "admin")
    await user.type(screen.getByLabelText(/^password$/i), "password123")
    await user.click(screen.getByRole("button", { name: /sign in/i }))

    await waitFor(() => {
      expect(toast.showToast).toHaveBeenCalledWith(
        expect.objectContaining({
          color: "red",
          message: expect.stringContaining("session cookie was not stored"),
        }),
      )
    })
  })
})
