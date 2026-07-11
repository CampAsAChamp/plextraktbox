import { notifications } from "@mantine/notifications";
import type { ConnectionSummary, ConnectionTestResult } from "../../api/connections";

export const SAVED_SECRET_PLACEHOLDER = "••••••••••••";

export function isSavedSecretPlaceholder(value: string): boolean {
  return value === SAVED_SECRET_PLACEHOLDER;
}

export function isConnectionConfigured(connection: ConnectionSummary | undefined): boolean {
  return connection !== undefined && connection.status !== "unconfigured";
}

export function savedUsername(connection: ConnectionSummary | undefined): string {
  if (!isConnectionConfigured(connection)) return "";
  const value = connection?.config.username;
  return typeof value === "string" ? value : "";
}

export function showConnectionTestResult(result: ConnectionTestResult) {
  notifications.show({
    color: result.ok ? "green" : "red",
    message: result.message,
  });
}

export function secretPlaceholderHandlers(
  value: string,
  setValue: (next: string) => void,
  configured: boolean,
) {
  return {
    onFocus: () => {
      if (isSavedSecretPlaceholder(value)) setValue("");
    },
    onBlur: () => {
      if (value === "" && configured) setValue(SAVED_SECRET_PLACEHOLDER);
    },
  };
}

export function secretPlaceholderInputProps(
  value: string,
  setValue: (next: string) => void,
  configured: boolean,
  placeholderWhenSaved: string,
  savedDescription: string,
) {
  const isSavedPlaceholder = isSavedSecretPlaceholder(value);
  const handlers = secretPlaceholderHandlers(value, setValue, configured);

  return {
    value,
    onFocus: handlers.onFocus,
    onBlur: handlers.onBlur,
    placeholder: configured ? placeholderWhenSaved : undefined,
    description: isSavedPlaceholder ? savedDescription : undefined,
    styles: isSavedPlaceholder ? { visibilityToggle: { display: "none" } } : undefined,
  };
}
