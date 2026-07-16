import { screen } from "@testing-library/react"
import { expect, test } from "vitest"

import { RunStatusBadge } from "src/components/runs/RunBadges"
import { renderWithProviders } from "tests/render"

test("pulses running status when pulse is enabled", () => {
  renderWithProviders(<RunStatusBadge status="running" pulse />)
  expect(screen.getByText("running").closest(".mantine-Badge-root")).toHaveClass("ptbPulseOpacity")
})

test("does not pulse running status by default", () => {
  renderWithProviders(<RunStatusBadge status="running" />)
  expect(screen.getByText("running").closest(".mantine-Badge-root")).not.toHaveClass("ptbPulseOpacity")
})

test("does not pulse non-running statuses even when pulse is enabled", () => {
  renderWithProviders(<RunStatusBadge status="success" pulse />)
  expect(screen.getByText("success").closest(".mantine-Badge-root")).not.toHaveClass("ptbPulseOpacity")
})
