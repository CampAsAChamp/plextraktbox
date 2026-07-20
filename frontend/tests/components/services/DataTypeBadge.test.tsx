import { screen } from "@testing-library/react"
import { expect, test } from "vitest"

import { DataTypeBadge } from "src/components/services/DataTypeBadge"
import { renderWithProviders } from "tests/render"

test("label mode shows data type text", () => {
  renderWithProviders(<DataTypeBadge dataType="watchlist" />)
  expect(screen.getByText("Watchlist")).toBeInTheDocument()
})

test("responsive mode exposes aria-label for data type", () => {
  renderWithProviders(<DataTypeBadge dataType="ratings" mode="responsive" />)
  expect(screen.getByLabelText("Ratings")).toBeInTheDocument()
})
