/** Dev-friendly console logger with level-based styling in the browser. */

export type LogLevel = "debug" | "info" | "warn" | "error";

const LEVEL_STYLE: Record<LogLevel, string> = {
  debug: "color:#9ca3af",
  info: "color:#60a5fa",
  warn: "color:#fbbf24;font-weight:600",
  error: "color:#f87171;font-weight:600",
};

const LEVEL_METHOD: Record<LogLevel, "debug" | "info" | "warn" | "error"> = {
  debug: "debug",
  info: "info",
  warn: "warn",
  error: "error",
};

function emit(level: LogLevel, message: string, context?: Record<string, unknown>): void {
  if (!import.meta.env.DEV) return;

  const prefix = `%c${level.toUpperCase()}%c ${message}`;
  const args: unknown[] = [prefix, LEVEL_STYLE[level], "color:inherit"];

  if (context && Object.keys(context).length > 0) {
    args.push(context);
  }

  console[LEVEL_METHOD[level]](...args);
}

export const logger = {
  debug: (message: string, context?: Record<string, unknown>) => emit("debug", message, context),
  info: (message: string, context?: Record<string, unknown>) => emit("info", message, context),
  warn: (message: string, context?: Record<string, unknown>) => emit("warn", message, context),
  error: (message: string, context?: Record<string, unknown>) => emit("error", message, context),
};
