/**
 * Nord palette mapping for Mantine.
 *
 * Colors from https://www.nordtheme.com/docs/colors-and-palettes (MIT).
 */
import { createTheme, type MantineColorsTuple } from "@mantine/core";
import { sharedTheme } from "src/themes/shared";
import type { BuiltinThemeDefinition } from "src/themes/types";

/** Nord frost / polar — primary around `#88C0D0` / `#81A1C1`. */
const cyan: MantineColorsTuple = [
  "#E5F0F4",
  "#C8DFE8",
  "#A3CBDA",
  "#88C0D0",
  "#81A1C1",
  "#5E81AC",
  "#4C6A90",
  "#3B5473",
  "#2A3B52",
  "#1A2534",
];

/** Nord polar night surfaces. */
const dark: MantineColorsTuple = [
  "#ECEFF4",
  "#E5E9F0",
  "#D8DEE9",
  "#A5ADBA",
  "#7B8494",
  "#4C566A",
  "#434C5E",
  "#3B4252",
  "#2E3440",
  "#242933",
];

export const nordTheme = createTheme({
  ...sharedTheme,
  primaryColor: "cyan",
  colors: {
    cyan,
    dark,
  },
  black: "#242933",
  white: "#ECEFF4",
  defaultGradient: { from: "cyan.3", to: "cyan.5", deg: 135 },
  other: {
    ...sharedTheme.other,
    bodyGradient: "linear-gradient(165deg, #242933 0%, #2E3440 42%, #3B4252 100%)",
  },
});

export const nordDefinition: BuiltinThemeDefinition = {
  id: "nord",
  name: "Nord",
  swatches: ["#2E3440", "#3B4252", "#88C0D0"],
  theme: nordTheme,
};
