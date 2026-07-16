/* Provider modules export the hook alongside the provider — Fast Refresh is fine here. */
/* eslint-disable react-refresh/only-export-components */
import { createContext, type ReactNode, useCallback, useContext, useMemo, useState } from "react"

import {
  type DateFormatPreference,
  DEFAULT_DISPLAY_PREFERENCES,
  type DisplayPreferences,
  loadDisplayPreferences,
  saveDisplayPreferences,
  type TimeFormatPreference,
  type TimezonePreference,
} from "src/settings/displayPreferences"
import { showToast } from "src/toast"

type DisplayPreferencesContextValue = {
  preferences: DisplayPreferences
  setTimezone: (timezone: TimezonePreference) => void
  setTimeFormat: (timeFormat: TimeFormatPreference) => void
  setDateFormat: (dateFormat: DateFormatPreference) => void
}

const DisplayPreferencesContext = createContext<DisplayPreferencesContextValue | null>(null)

function preferencesEqual(a: DisplayPreferences, b: DisplayPreferences): boolean {
  return a.timezone === b.timezone && a.timeFormat === b.timeFormat && a.dateFormat === b.dateFormat
}

export function DisplayPreferencesProvider({ children }: { children: ReactNode }) {
  const [preferences, setPreferences] = useState<DisplayPreferences>(() => loadDisplayPreferences())

  const updatePreferences = useCallback((patch: Partial<DisplayPreferences>) => {
    let didChange = false
    setPreferences((current) => {
      const next = { ...current, ...patch }
      if (preferencesEqual(current, next)) {
        return current
      }
      didChange = true
      saveDisplayPreferences(next)
      return next
    })
    if (didChange) {
      showToast({
        color: "green",
        message: "Settings saved",
      })
    }
  }, [])

  const value = useMemo(
    () => ({
      preferences,
      setTimezone: (timezone: TimezonePreference) => updatePreferences({ timezone }),
      setTimeFormat: (timeFormat: TimeFormatPreference) => updatePreferences({ timeFormat }),
      setDateFormat: (dateFormat: DateFormatPreference) => updatePreferences({ dateFormat }),
    }),
    [preferences, updatePreferences],
  )

  return <DisplayPreferencesContext.Provider value={value}>{children}</DisplayPreferencesContext.Provider>
}

export function useDisplayPreferences() {
  const context = useContext(DisplayPreferencesContext)
  if (!context) {
    return {
      preferences: DEFAULT_DISPLAY_PREFERENCES,
      setTimezone: () => {},
      setTimeFormat: () => {},
      setDateFormat: () => {},
    }
  }
  return context
}
