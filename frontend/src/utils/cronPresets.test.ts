import { describe, expect, it } from "vitest"

import { isValidCronExpression } from "src/utils/cron"
import { CRON_PRESETS, matchCronPreset } from "src/utils/cronPresets"

describe("cron presets", () => {
  it("uses valid cron expressions", () => {
    for (const preset of CRON_PRESETS) {
      expect(isValidCronExpression(preset.cron)).toBe(true)
    }
  })

  it("matches known presets", () => {
    expect(matchCronPreset("0 3 * * *")).toBe("daily-3am")
    expect(matchCronPreset("0 */6 * * *")).toBe("every-6h")
    expect(matchCronPreset("0 3 * * 0")).toBe("weekly")
    expect(matchCronPreset("0 4 * * *")).toBeNull()
  })
})
