/**
 * Atom One Dark Pro palette mapping for Mantine.
 *
 * Colors based on Binaryify/OneDark-Pro (VS Code), itself derived from Atom One Dark.
 * https://github.com/Binaryify/OneDark-Pro
 */
import { createTheme, type MantineColorsTuple } from "@mantine/core";
import { sharedTheme } from "src/themes/shared";
import type { BuiltinThemeDefinition } from "src/themes/types";

/** Soft blue primary — One Dark Pro function/accent `#61afef`. */
const blue: MantineColorsTuple = [
  "#E8F1FC",
  "#C5DBF7",
  "#9FC3F0",
  "#7AABE8",
  "#61AFEF",
  "#4D8FD4",
  "#3D73B0",
  "#2E5785",
  "#1F3B5A",
  "#12203A",
];

/** One Dark Pro surfaces — `#282c34` editor bg family. */
const dark: MantineColorsTuple = [
  "#ABB2BF",
  "#9DA5B4",
  "#7F848E",
  "#5C6370",
  "#4B5263",
  "#3E4452",
  "#2C313C",
  "#282C34",
  "#21252B",
  "#1B1F25",
];

export const oneDarkProTheme = createTheme({
  ...sharedTheme,
  primaryColor: "blue",
  colors: {
    blue,
    dark,
  },
  black: "#1B1F25",
  white: "#ABB2BF",
  defaultGradient: { from: "blue.4", to: "blue.6", deg: 135 },
  other: {
    ...sharedTheme.other,
    bodyGradient: "linear-gradient(165deg, #1B1F25 0%, #21252B 42%, #282C34 100%)",
  },
});

export const oneDarkProDefinition: BuiltinThemeDefinition = {
  id: "one-dark-pro",
  name: "Atom One Dark Pro",
  swatches: ["#282C34", "#21252B", "#61AFEF"],
  theme: oneDarkProTheme,
};
