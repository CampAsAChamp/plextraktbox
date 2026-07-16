import { MantineProvider } from "@mantine/core"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { render } from "@testing-library/react"
import type { ReactElement } from "react"
import { MemoryRouter } from "react-router-dom"

import { DisplayPreferencesProvider } from "src/settings/DisplayPreferencesProvider"
import { theme } from "src/theme"

// Wraps a component in the same providers as the real app so tests exercise it
// the way it actually runs.
export function renderWithProviders(ui: ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return render(
    <MantineProvider theme={theme} forceColorScheme="dark">
      <QueryClientProvider client={queryClient}>
        <DisplayPreferencesProvider>
          <MemoryRouter>{ui}</MemoryRouter>
        </DisplayPreferencesProvider>
      </QueryClientProvider>
    </MantineProvider>,
  )
}
