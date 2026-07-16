import { MantineProvider } from "@mantine/core"
import { Notifications } from "@mantine/notifications"
import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { afterEach, expect, test, vi } from "vitest"

import { CopyAction } from "src/components/CopyAction"
import { theme } from "src/theme"

afterEach(() => {
  vi.unstubAllGlobals()
})

test("swaps to a check icon after copying", async () => {
  const user = userEvent.setup()
  vi.stubGlobal("navigator", {
    ...navigator,
    clipboard: {
      writeText: vi.fn().mockResolvedValue(undefined),
    },
  })

  render(
    <MantineProvider theme={theme} forceColorScheme="dark">
      <Notifications />
      <CopyAction value="hello" label="Copy value" />
    </MantineProvider>,
  )

  await user.click(screen.getByRole("button", { name: "Copy value" }))

  expect(screen.getByRole("button", { name: "Copy value" }).querySelector("svg")).not.toBeNull()
  expect(screen.getByRole("button", { name: "Copy value" }).querySelector(".ptbIconPop, [class*='iconEnter']")).not.toBeNull()
})
