import type { LogEntry } from "../../api/logs";

export const LOG_LOGGER_BRACKET_COLOR = "#808080";
export const LOG_LOGGER_NAME_COLOR = "#4ec9b0";

export function isJsonLikeString(value: string): boolean {
  const trimmed = value.trim();
  return (
    (trimmed.startsWith("{") && trimmed.endsWith("}")) ||
    (trimmed.startsWith("[") && trimmed.endsWith("]"))
  );
}

export function formatContextValue(value: unknown): string {
  if (value === null) return "null";
  if (value === undefined) return "undefined";
  if (typeof value === "object") {
    return JSON.stringify(value, null, 2);
  }
  if (typeof value === "string" && isJsonLikeString(value)) {
    try {
      return JSON.stringify(JSON.parse(value), null, 2);
    } catch {
      return value;
    }
  }
  if (typeof value === "string") return value;
  return JSON.stringify(value);
}

export function formatContextValueCompact(value: unknown, maxLength = 120): string {
  if (value === null) return "null";
  if (value === undefined) return "undefined";
  if (typeof value === "object") {
    return truncateCompactJson(JSON.stringify(value), maxLength);
  }
  if (typeof value === "string" && isJsonLikeString(value)) {
    try {
      return truncateCompactJson(JSON.stringify(JSON.parse(value)), maxLength);
    } catch {
      return value;
    }
  }
  if (typeof value === "string") return value;
  return truncateCompactJson(JSON.stringify(value), maxLength);
}

function truncateCompactJson(value: string, maxLength: number): string {
  if (value.length <= maxLength) return value;
  return `${value.slice(0, maxLength)}…`;
}

export function hasExpandableContext(context: Record<string, unknown>): boolean {
  return Object.keys(logContextForDisplay(context)).length > 0;
}

export function formatLogDisplayMessage(line: LogEntry): string {
  const contextual = line.context.message;
  if (typeof contextual === "string" && contextual.trim()) {
    return contextual;
  }
  return line.message;
}

export function logContextForDisplay(
  context: Record<string, unknown>,
): Record<string, unknown> {
  const contextual = context.message;
  if (typeof contextual !== "string" || !contextual.trim()) {
    return context;
  }
  const { message: _message, ...rest } = context;
  return rest;
}

export function shouldPrettyPrintContextValue(value: unknown): boolean {
  const formatted = formatContextValue(value);
  return formatted.includes("\n") || formatted.length > 80;
}

const RUN_LOG_STATUS_VALUES = new Set(["success", "failed", "partial", "running"]);

export function shouldRenderStatusBadge(key: string, value: unknown): value is string {
  return key === "status" && typeof value === "string" && RUN_LOG_STATUS_VALUES.has(value);
}

export function shouldSyntaxHighlightContextValue(value: unknown): boolean {
  if (value === null || value === undefined) return true;
  if (typeof value === "object") return true;
  if (typeof value === "boolean" || typeof value === "number") return true;
  if (typeof value === "string") {
    return isJsonLikeString(value) || value === "true" || value === "false" || value === "null";
  }
  return false;
}

export function estimateLogLineHeight(line: LogEntry, expanded = false): number {
  const collapsedHeight = 32;
  if (!expanded) return collapsedHeight;

  const base = 34;
  const entries = Object.entries(line.context);
  if (entries.length === 0) return base;

  let height = base;
  for (const [, value] of entries) {
    const formatted = formatContextValue(value);
    if (shouldPrettyPrintContextValue(value)) {
      height += 18 + formatted.split("\n").length * 15 + 8;
    } else {
      height += 18;
    }
  }
  return height;
}
