/**
 * Dracula palette mapping for Mantine.
 *
 * Colors from https://draculatheme.com/contribute (MIT).
 */
import { createTheme, type MantineColorsTuple } from "@mantine/core";
import { sharedTheme } from "src/themes/shared";
import type { BuiltinThemeDefinition } from "src/themes/types";

/** Dracula purple primary — `#BD93F9`. */
const violet: MantineColorsTuple = [
  "#F3EBFE",
  "#E4D4FC",
  "#D4BBFA",
  "#BD93F9",
  "#A87EF0",
  "#8B6ACF",
  "#6E53A8",
  "#533D80",
  "#3A2B59",
  "#241A38",
];

/** Dracula background family — `#282A36`. */
const dark: MantineColorsTuple = [
  "#F8F8F2",
  "#E2E2DC",
  "#BFBFC9",
  "#9A9AA8",
  "#72728A",
  "#44475A",
  "#383A4C",
  "#282A36",
  "#21222C",
  "#191A21",
];

export const draculaTheme = createTheme({
  ...sharedTheme,
  primaryColor: "violet",
  colors: {
    violet,
    dark,
  },
  black: "#191A21",
  white: "#F8F8F2",
  defaultGradient: { from: "violet.3", to: "violet.5", deg: 135 },
  other: {
    ...sharedTheme.other,
    bodyGradient: "linear-gradient(165deg, #191A21 0%, #21222C 42%, #282A36 100%)",
  },
});

export const draculaDefinition: BuiltinThemeDefinition = {
  id: "dracula",
  name: "Dracula",
  swatches: ["#282A36", "#44475A", "#BD93F9"],
  theme: draculaTheme,
};
