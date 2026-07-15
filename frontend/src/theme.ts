import { createTheme, type MantineColorsTuple } from "@mantine/core";

/** Warm amber primary — film-light accent for the cinema-night baseline. */
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
];

/** Cool charcoal surfaces — replaces stock Mantine dark. */
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
];

const fontFamily =
  "Nunito, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica, Arial, sans-serif";

/**
 * Permanent product baseline UI (pill-max cinema night).
 * Not a selectable theme — the only look passed to MantineProvider.
 */
export const theme = createTheme({
  primaryColor: "amber",
  defaultRadius: "lg",
  fontFamily,
  headings: { fontFamily },
  radius: {
    xs: "10px",
    sm: "14px",
    md: "18px",
    lg: "24px",
    xl: "9999px",
  },
  colors: {
    amber,
    dark,
  },
  black: "#0E1117",
  white: "#EEF1F6",
  defaultGradient: { from: "amber.5", to: "amber.7", deg: 135 },
  components: {
    Button: {
      defaultProps: { radius: "xl" },
      styles: {
        root: {
          transition: "filter 160ms ease, background-color 160ms ease",
        },
      },
    },
    ActionIcon: {
      defaultProps: { radius: "xl" },
      styles: {
        root: {
          transition: "filter 160ms ease, background-color 160ms ease",
        },
      },
    },
    Badge: { defaultProps: { radius: "xl" } },
    // NavLink has no radius prop — border-radius must be set via styles.
    NavLink: {
      styles: {
        root: {
          borderRadius: "var(--mantine-radius-xl)",
          transition: "background-color 160ms ease, color 160ms ease",
        },
      },
    },
    TextInput: { defaultProps: { radius: "xl" } },
    PasswordInput: { defaultProps: { radius: "xl" } },
    Select: { defaultProps: { radius: "xl" } },
    NumberInput: { defaultProps: { radius: "xl" } },
    PillsInput: { defaultProps: { radius: "xl" } },
    Pill: { defaultProps: { radius: "xl" } },
    Textarea: { defaultProps: { radius: "lg" } },
    SegmentedControl: { defaultProps: { radius: "xl" } },
    Menu: {
      defaultProps: { radius: "lg" },
      styles: {
        item: { borderRadius: "var(--mantine-radius-xl)" },
        dropdown: { borderRadius: "var(--mantine-radius-lg)" },
      },
    },
    Tooltip: { defaultProps: { radius: "xl" } },
    Checkbox: { defaultProps: { radius: "sm" } },
    Radio: { defaultProps: { radius: "xl" } },
    Combobox: {
      styles: {
        dropdown: { borderRadius: "var(--mantine-radius-lg)" },
        option: { borderRadius: "var(--mantine-radius-xl)" },
      },
    },
    Paper: { defaultProps: { radius: "lg" } },
    Alert: { defaultProps: { radius: "lg" } },
    Modal: { defaultProps: { radius: "lg" } },
    Popover: { defaultProps: { radius: "lg" } },
    Notification: { defaultProps: { radius: "lg" } },
    Accordion: {
      defaultProps: { radius: "lg" },
      styles: {
        control: { borderRadius: "var(--mantine-radius-lg)" },
        item: { borderRadius: "var(--mantine-radius-lg)" },
      },
    },
    Table: {
      styles: {
        th: {
          backgroundColor: "var(--mantine-color-dark-5)",
          color: "var(--mantine-color-dark-1)",
          borderBottom: "1px solid var(--mantine-color-dark-4)",
          fontSize: "var(--mantine-font-size-xs)",
          fontWeight: 700,
          letterSpacing: "0.04em",
          textTransform: "uppercase",
        },
        td: {
          borderBottomColor: "var(--mantine-color-dark-5)",
        },
      },
    },
    Code: { defaultProps: { radius: "md" } },
    ThemeIcon: { defaultProps: { radius: "xl" } },
    Indicator: { defaultProps: { radius: "xl" } },
    ScrollArea: {
      styles: {
        viewport: { borderRadius: "inherit" },
      },
    },
    AppShell: {
      styles: {
        header: {
          backgroundColor: "color-mix(in srgb, var(--mantine-color-dark-8) 88%, transparent)",
          borderBottomColor: "var(--mantine-color-dark-5)",
          backdropFilter: "blur(8px)",
        },
      },
    },
  },
});
