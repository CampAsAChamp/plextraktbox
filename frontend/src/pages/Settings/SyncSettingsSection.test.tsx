import { screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import * as settingsApi from "src/api/settings"
import { SyncSettingsSection } from "src/pages/Settings/SyncSettingsSection"
import { renderWithProviders } from "src/test/render"
import * as toast from "src/toast"

const baseSettings: settingsApi.AppSettings = {
  default_cron: "0 3 * * *",
  cron_timezone: "UTC",
  cron_timezone_resolved: "UTC",
  log_retention_days: 30,
  global_dry_run: true,
  exclude_ids: { tmdb: [], imdb: [], tvdb: [] },
  ui_theme: "atom-one-dark-pro",
  letterboxd_export_cache_ttl_hours: 24,
  trakt_list_cache_ttl_minutes: 30,
}

beforeEach(() => {
  vi.spyOn(toast, "showToast").mockImplementation(() => undefined)
  vi.spyOn(settingsApi, "getSettings").mockResolvedValue(baseSettings)
  vi.spyOn(settingsApi, "updateSettings").mockImplementation(async (input) => ({
    ...baseSettings,
    ...input,
    cron_timezone_resolved:
      input.cron_timezone === "local" ? (input.cron_local_zone ?? "UTC") : input.cron_timezone === "UTC" ? "UTC" : input.cron_timezone,
  }))
})

afterEach(() => {
  vi.restoreAllMocks()
})

describe("SyncSettingsSection cron timezone", () => {
  it("saves immediately and toasts when Local is selected", async () => {
    const user = userEvent.setup()
    renderWithProviders(<SyncSettingsSection />)

    // Wait until settings hydrate — persistCronTimezone no-ops while data is undefined,
    // and the SegmentedControl stays disabled during isLoading (flaky under full-suite load).
    const localRadio = await screen.findByRole("radio", { name: /Local/i })
    await waitFor(() => {
      expect(localRadio).toBeEnabled()
    })

    await user.click(localRadio)

    await waitFor(() => {
      expect(settingsApi.updateSettings).toHaveBeenCalledWith(
        expect.objectContaining({
          cron_timezone: "local",
          cron_local_zone: expect.any(String),
        }),
      )
    })
    expect(toast.showToast).toHaveBeenCalledWith(expect.objectContaining({ color: "green", message: "Cron timezone saved" }))
  })
})
