export type LogLevel = "debug" | "info" | "warning" | "error"

export const LOG_LEVEL_OPTIONS: { value: LogLevel; label: string }[] = [
  { value: "debug", label: "Debug" },
  { value: "info", label: "Info" },
  { value: "warning", label: "Warn" },
  { value: "error", label: "Error" },
]
