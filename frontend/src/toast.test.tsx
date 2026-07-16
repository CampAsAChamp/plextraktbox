import { notifications } from "@mantine/notifications"
import { cleanup, render } from "@testing-library/react"
import { afterEach, describe, expect, it, vi } from "vitest"

import { iconForToastColor, showToast } from "src/toast"

vi.mock("@mantine/notifications", () => ({
  notifications: {
    show: vi.fn(),
  },
}))

afterEach(() => {
  cleanup()
  vi.clearAllMocks()
})

describe("iconForToastColor", () => {
  it("maps success, error, warning, and info colors to distinct icons", () => {
    const green = render(<>{iconForToastColor("green")}</>).container.querySelector("svg")
    const red = render(<>{iconForToastColor("red")}</>).container.querySelector("svg")
    const orange = render(<>{iconForToastColor("orange")}</>).container.querySelector("svg")
    const blue = render(<>{iconForToastColor("blue")}</>).container.querySelector("svg")

    expect(green?.innerHTML).toContain("polyline")
    expect(red?.innerHTML).toContain("line")
    expect(orange?.innerHTML).toContain("path")
    expect(blue?.innerHTML).toContain("circle")
  })
})

describe("showToast", () => {
  it("adds a matching icon and defaults color to blue", () => {
    showToast({ message: "Hello" })

    expect(notifications.show).toHaveBeenCalledWith(
      expect.objectContaining({
        color: "blue",
        message: "Hello",
        icon: expect.anything(),
      }),
    )
  })

  it("preserves an explicit icon", () => {
    const icon = <span data-testid="custom-icon" />
    showToast({ color: "green", message: "Saved", icon })

    expect(notifications.show).toHaveBeenCalledWith(
      expect.objectContaining({
        color: "green",
        icon,
      }),
    )
  })
})
