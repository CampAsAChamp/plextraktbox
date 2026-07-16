/** Cinema Night — amber primary + cool charcoal surfaces (former product baseline). */
import { createTheme, type MantineColorsTuple } from "@mantine/core"

import { sharedTheme } from "src/themes/shared"
import type { BuiltinThemeDefinition } from "src/themes/types"

const amber: MantineColorsTuple = [
  "#FFF8EB",
  "#FFE8C2",
  "#FFD699",
  "#F5C06A",
  "#E8A54B",
  "#D4913A",
  "#B8782E",
  "#8F5C24",
  "#66431B",
  "#3D2810",
]

const dark: MantineColorsTuple = [
  "#EEF1F6",
  "#C5CAD6",
  "#9AA3B5",
  "#6B7489",
  "#454E61",
  "#343E4F",
  "#252D3A",
  "#1C232E",
  "#14181F",
  "#0E1117",
]

export const cinemaNightTheme = createTheme({
  ...sharedTheme,
  primaryColor: "amber",
  colors: {
    amber,
    dark,
  },
  black: "#0E1117",
  white: "#EEF1F6",
  defaultGradient: { from: "amber.5", to: "amber.7", deg: 135 },
  other: {
    ...sharedTheme.other,
    bodyGradient:
      "linear-gradient(165deg, var(--mantine-color-dark-9) 0%, var(--mantine-color-dark-8) 42%, var(--mantine-color-dark-7) 100%)",
  },
})

export const cinemaNightDefinition: BuiltinThemeDefinition = {
  id: "cinema-night",
  name: "Cinema Night",
  swatches: ["#0E1117", "#1C232E", "#D4913A"],
  theme: cinemaNightTheme,
}
