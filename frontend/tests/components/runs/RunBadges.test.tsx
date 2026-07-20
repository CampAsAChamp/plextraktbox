import { screen } from "@testing-library/react"
import { expect, test } from "vitest"

import { DryRunBadge, RunStatusBadge, RunTriggerBadge } from "src/components/runs/RunBadges"
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

test("responsive status badge exposes aria-label on the circular icon badge", () => {
  renderWithProviders(<RunStatusBadge status="success" mode="responsive" />)
  expect(screen.getByLabelText("success")).toBeInTheDocument()
  expect(screen.getByText("success")).toBeInTheDocument()
})

test("responsive trigger badge exposes aria-label", () => {
  renderWithProviders(<RunTriggerBadge trigger="scheduled" mode="responsive" />)
  expect(screen.getByLabelText("scheduled")).toBeInTheDocument()
})

test("responsive compact dry-run badge exposes aria-label", () => {
  renderWithProviders(<DryRunBadge dryRun compact mode="responsive" />)
  expect(screen.getByLabelText("yes")).toBeInTheDocument()
})

test("label mode does not set aria-label on the badge root", () => {
  renderWithProviders(<RunStatusBadge status="failed" />)
  expect(screen.queryByLabelText("failed")).not.toBeInTheDocument()
  expect(screen.getByText("failed")).toBeInTheDocument()
})
