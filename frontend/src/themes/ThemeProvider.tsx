import { MantineProvider, type MantineThemeOverride } from "@mantine/core";
import { useQuery } from "@tanstack/react-query";
import { type ReactNode, useEffect, useMemo, useState } from "react";
import { getSettings } from "src/api/settings";
import { fetchThemeCss } from "src/api/themes";
import { customThemeBase, getBuiltinTheme, isBuiltinThemeId } from "src/themes/registry";
import { readCachedThemeId, writeCachedThemeId } from "src/themes/themePreference";

const CUSTOM_STYLE_ID = "ptb-custom-theme";

function applyHtmlThemeAttr(themeId: string): void {
  document.documentElement.setAttribute("data-ptb-theme", themeId);
}

function applyBodyGradient(theme: MantineThemeOverride | undefined): void {
  const gradient =
    (theme?.other as { bodyGradient?: string } | undefined)?.bodyGradient ??
    "linear-gradient(165deg, var(--mantine-color-dark-9) 0%, var(--mantine-color-dark-8) 42%, var(--mantine-color-dark-7) 100%)";
  document.documentElement.style.setProperty("--ptb-body-gradient", gradient);
}

function injectCustomCss(css: string): void {
  let el = document.getElementById(CUSTOM_STYLE_ID) as HTMLStyleElement | null;
  if (!el) {
    el = document.createElement("style");
    el.id = CUSTOM_STYLE_ID;
    document.head.appendChild(el);
  }
  el.textContent = css;
}

function removeCustomCss(): void {
  document.getElementById(CUSTOM_STYLE_ID)?.remove();
}

interface ThemeProviderProps {
  children: ReactNode;
}

/**
 * Resolves the active UI theme from settings (with localStorage FOUC cache)
 * and wires MantineProvider + optional custom CSS inject.
 */
export function ThemeProvider({ children }: ThemeProviderProps) {
  const [themeId, setThemeId] = useState(readCachedThemeId);

  // Shared with Settings; 401 (setup/login) leaves cache empty — keep FOUC id.
  const settingsQuery = useQuery({
    queryKey: ["settings"],
    queryFn: getSettings,
    staleTime: 30_000,
    retry: false,
  });

  useEffect(() => {
    const fromServer = settingsQuery.data?.ui_theme;
    if (fromServer && fromServer !== themeId) {
      setThemeId(fromServer);
      writeCachedThemeId(fromServer);
    }
  }, [settingsQuery.data?.ui_theme, themeId]);

  const isCustom = Boolean(themeId) && !isBuiltinThemeId(themeId);

  const cssQuery = useQuery({
    queryKey: ["theme-css", themeId],
    queryFn: () => fetchThemeCss(themeId),
    enabled: isCustom,
    retry: false,
  });

  const mantineTheme = useMemo((): MantineThemeOverride => {
    const builtin = getBuiltinTheme(themeId);
    if (builtin) {
      return builtin.theme;
    }
    return customThemeBase;
  }, [themeId]);

  useEffect(() => {
    applyHtmlThemeAttr(themeId);
    applyBodyGradient(mantineTheme);
    writeCachedThemeId(themeId);
  }, [themeId, mantineTheme]);

  useEffect(() => {
    if (!isCustom) {
      removeCustomCss();
      return;
    }
    if (cssQuery.data) {
      injectCustomCss(cssQuery.data);
    }
  }, [isCustom, cssQuery.data]);

  // Missing/failed custom → fall back visually to One Dark Pro base without clearing setting here.
  useEffect(() => {
    if (isCustom && cssQuery.isError) {
      removeCustomCss();
      applyHtmlThemeAttr("one-dark-pro");
      applyBodyGradient(customThemeBase);
    }
  }, [isCustom, cssQuery.isError]);

  return (
    <MantineProvider theme={mantineTheme} forceColorScheme="dark">
      {children}
    </MantineProvider>
  );
}
