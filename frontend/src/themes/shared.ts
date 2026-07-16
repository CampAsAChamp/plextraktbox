import type { MantineThemeOverride } from "@mantine/core"

const fontFamily = "Nunito, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica, Arial, sans-serif"

/** Shared chrome (radius, typography, component overrides) across built-in themes. */
export const sharedTheme: MantineThemeOverride = {
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
  other: {
    bodyGradient:
      "linear-gradient(165deg, var(--mantine-color-dark-9) 0%, var(--mantine-color-dark-8) 42%, var(--mantine-color-dark-7) 100%)",
  },
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
      defaultProps: { radius: "sm" },
      styles: {
        item: { borderRadius: "var(--mantine-radius-xs)" },
        dropdown: { borderRadius: "var(--mantine-radius-sm)" },
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
    Notification: {
      defaultProps: { radius: "lg" },
      styles: {
        root: {
          backgroundColor: "color-mix(in srgb, var(--notification-color) 16%, var(--mantine-color-dark-6))",
          border: "1px solid color-mix(in srgb, var(--notification-color) 38%, transparent)",
        },
      },
    },
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
          paddingTop: "env(safe-area-inset-top)",
        },
        main: {
          paddingBottom: "calc(var(--mantine-spacing-md) + env(safe-area-inset-bottom))",
        },
      },
    },
    Drawer: {
      defaultProps: { radius: 0 },
      styles: {
        content: {
          paddingTop: "env(safe-area-inset-top)",
          paddingBottom: "env(safe-area-inset-bottom)",
        },
      },
    },
  },
}
