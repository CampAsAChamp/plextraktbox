import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from "react";
import {
  DEFAULT_DISPLAY_PREFERENCES,
  loadDisplayPreferences,
  saveDisplayPreferences,
  type DateFormatPreference,
  type DisplayPreferences,
  type TimeFormatPreference,
  type TimezonePreference,
} from "./displayPreferences";

type DisplayPreferencesContextValue = {
  preferences: DisplayPreferences;
  setTimezone: (timezone: TimezonePreference) => void;
  setTimeFormat: (timeFormat: TimeFormatPreference) => void;
  setDateFormat: (dateFormat: DateFormatPreference) => void;
};

const DisplayPreferencesContext = createContext<DisplayPreferencesContextValue | null>(null);

export function DisplayPreferencesProvider({ children }: { children: ReactNode }) {
  const [preferences, setPreferences] = useState<DisplayPreferences>(() => loadDisplayPreferences());

  const updatePreferences = useCallback((patch: Partial<DisplayPreferences>) => {
    setPreferences((current) => {
      const next = { ...current, ...patch };
      saveDisplayPreferences(next);
      return next;
    });
  }, []);

  const value = useMemo(
    () => ({
      preferences,
      setTimezone: (timezone: TimezonePreference) => updatePreferences({ timezone }),
      setTimeFormat: (timeFormat: TimeFormatPreference) => updatePreferences({ timeFormat }),
      setDateFormat: (dateFormat: DateFormatPreference) => updatePreferences({ dateFormat }),
    }),
    [preferences, updatePreferences],
  );

  return (
    <DisplayPreferencesContext.Provider value={value}>{children}</DisplayPreferencesContext.Provider>
  );
}

export function useDisplayPreferences() {
  const context = useContext(DisplayPreferencesContext);
  if (!context) {
    return {
      preferences: DEFAULT_DISPLAY_PREFERENCES,
      setTimezone: () => {},
      setTimeFormat: () => {},
      setDateFormat: () => {},
    };
  }
  return context;
}
