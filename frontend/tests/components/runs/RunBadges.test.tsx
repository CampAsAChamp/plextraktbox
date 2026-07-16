import { screen } from "@testing-library/react"
import { expect, test } from "vitest"

import { RunStatusBadge } from "src/components/runs/RunBadges"
import { renderWithProviders } from "tests/render"

test("applies pulse class when status is running", () => {
  renderWithProviders(<RunStatusBadge status="running" />)
  expect(screen.getByText("running").closest(".mantine-Badge-root")).toHaveClass("ptbPulseOpacity")
})

test("does not pulse non-running statuses", () => {
  renderWithProviders(<RunStatusBadge status="success" />)
  expect(screen.getByText("success").closest(".mantine-Badge-root")).not.toHaveClass("ptbPulseOpacity")
})
