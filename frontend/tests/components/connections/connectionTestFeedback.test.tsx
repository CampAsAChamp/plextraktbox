import { MantineProvider } from "@mantine/core"
import { Notifications } from "@mantine/notifications"
import { render, screen } from "@testing-library/react"
import { act, renderHook } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { describe, expect, it, vi } from "vitest"

import { TestConnectionButton } from "src/components/connections/connectionTestFeedback"
import { useConnectionTestFeedback } from "src/components/connections/useConnectionTestFeedback"
import { theme } from "src/theme"

function renderButton(testStatus: "idle" | "success" | "error") {
  return render(
    <MantineProvider theme={theme} forceColorScheme="dark">
      <Notifications />
      <TestConnectionButton testStatus={testStatus} onClick={() => undefined} />
    </MantineProvider>,
  )
}

describe("TestConnectionButton", () => {
  it("shows a status icon after a successful test", () => {
    renderButton("success")

    const button = screen.getByRole("button", { name: /test connection/i })
    expect(button.querySelector("svg")).not.toBeNull()
    expect(button.querySelector("[class*='iconPop']")).not.toBeNull()
  })

  it("shows a status icon after a failed test", () => {
    renderButton("error")

    const button = screen.getByRole("button", { name: /test connection/i })
    expect(button.querySelector("svg")).not.toBeNull()
    expect(button.querySelector("[class*='iconPop']")).not.toBeNull()
  })

  it("shows a test icon before testing", () => {
    renderButton("idle")

    const button = screen.getByRole("button", { name: /test connection/i })
    expect(button.querySelector("svg")).not.toBeNull()
    expect(button.querySelector("[class*='iconPop']")).toBeNull()
  })

  it("calls onClick when pressed", async () => {
    const user = userEvent.setup()
    let clicked = false

    render(
      <MantineProvider theme={theme} forceColorScheme="dark">
        <TestConnectionButton testStatus="idle" onClick={() => (clicked = true)} />
      </MantineProvider>,
    )

    await user.click(screen.getByRole("button", { name: /test connection/i }))

    expect(clicked).toBe(true)
  })
})

describe("useConnectionTestFeedback", () => {
  it("returns the button to idle after a successful test", () => {
    vi.useFakeTimers()
    const { result } = renderHook(() => useConnectionTestFeedback())

    act(() => {
      result.current.onTestSuccess({ ok: true, message: "Connected" })
    })
    expect(result.current.testStatus).toBe("success")

    act(() => {
      vi.advanceTimersByTime(1500)
    })
    expect(result.current.testStatus).toBe("idle")

    vi.useRealTimers()
  })

  it("keeps the button in error state after a failed test", () => {
    const { result } = renderHook(() => useConnectionTestFeedback())

    act(() => {
      result.current.onTestSuccess({ ok: false, message: "Invalid credentials" })
    })

    expect(result.current.testStatus).toBe("error")
  })
})
