import { screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import { LetterboxdStep } from "src/components/connections/steps/LetterboxdStep"
import { renderWithProviders } from "tests/render"

function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  })
}

async function expandFlaresolverr(user: ReturnType<typeof userEvent.setup>) {
  await user.click(screen.getByRole("button", { name: /cloudflare \/ flaresolverr/i }))
}

describe("LetterboxdStep", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn())
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it("hides FlareSolverr fields behind a collapsed accordion by default", () => {
    renderWithProviders(<LetterboxdStep connection={undefined} onSaved={() => undefined} onCleared={() => undefined} />)

    const control = screen.getByRole("button", { name: /cloudflare \/ flaresolverr/i })
    expect(control).toHaveAttribute("aria-expanded", "false")
  })

  it("includes FlareSolverr fields in the save payload", async () => {
    // No per-keystroke delay — typing many fields is slow under full-suite load.
    const user = userEvent.setup({ delay: null })
    const fetchMock = vi.mocked(fetch)
    fetchMock.mockResolvedValue(
      jsonResponse({
        service: "letterboxd",
        status: "ok",
        config: {
          username: "nick",
          flaresolverr_url: "http://fs.local",
          flaresolverr_timeout_ms: 45000,
        },
        token_expires_at: null,
      }),
    )

    const onSaved = vi.fn()
    renderWithProviders(<LetterboxdStep connection={undefined} onSaved={onSaved} onCleared={() => undefined} />)

    await user.type(screen.getByLabelText(/letterboxd username/i), "nick")
    await user.type(screen.getByLabelText(/letterboxd password/i), "secret")
    await expandFlaresolverr(user)
    await user.type(screen.getByLabelText(/flaresolverr url/i), "http://fs.local/")
    await user.clear(screen.getByLabelText(/flaresolverr timeout/i))
    await user.type(screen.getByLabelText(/flaresolverr timeout/i), "45000")

    await user.click(screen.getByRole("button", { name: /save letterboxd connection/i }))

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalled()
    })

    const saveCall = fetchMock.mock.calls.find(([url]) => String(url).includes("/connections/letterboxd"))
    expect(saveCall).toBeDefined()
    const init = saveCall?.[1] as RequestInit | undefined
    const payload = JSON.parse(String(init?.body)) as Record<string, unknown>
    expect(payload.username).toBe("nick")
    expect(payload.password).toBe("secret")
    expect(payload.flaresolverr_url).toBe("http://fs.local/")
    expect(payload.flaresolverr_timeout_ms).toBe(45000)
    await waitFor(() => expect(onSaved).toHaveBeenCalled())
  }, 15_000)

  it("opens FlareSolverr and prefills fields when already configured", () => {
    renderWithProviders(
      <LetterboxdStep
        connection={{
          service: "letterboxd",
          status: "ok",
          config: {
            username: "nick",
            flaresolverr_url: "http://saved-fs.local",
            flaresolverr_timeout_ms: 30000,
          },
          token_expires_at: null,
        }}
        onSaved={() => undefined}
        onCleared={() => undefined}
      />,
    )

    expect(screen.getByText("Configured")).toBeInTheDocument()
    expect(screen.getByLabelText(/flaresolverr url/i)).toHaveValue("http://saved-fs.local")
    expect(screen.getByLabelText(/flaresolverr timeout/i)).toHaveValue("30000")
  })
})
