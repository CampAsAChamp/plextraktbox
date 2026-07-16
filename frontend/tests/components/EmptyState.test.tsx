import { screen } from "@testing-library/react"
import { expect, test } from "vitest"

import { EmptyState } from "src/components/EmptyState"
import { renderWithProviders } from "tests/render"

test("wraps children with empty-state reveal class", () => {
  renderWithProviders(
    <EmptyState>
      <span>No jobs yet</span>
    </EmptyState>,
  )

  expect(screen.getByText("No jobs yet").parentElement).toHaveClass("ptbEmptyIn")
})
