import { Badge, CloseButton, Group } from "@mantine/core";

export type LogLevel = "debug" | "info" | "warning" | "error";

export const LOG_LEVEL_OPTIONS: { value: LogLevel; label: string }[] = [
  { value: "debug", label: "Debug" },
  { value: "info", label: "Info" },
  { value: "warning", label: "Warn" },
  { value: "error", label: "Error" },
];

const LEVEL_COLORS: Record<string, string> = {
  debug: "gray",
  info: "blue",
  warning: "yellow",
  warn: "yellow",
  error: "red",
  critical: "red",
};

function CheckIcon({ size = 14 }: { size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="3"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden
    >
      <polyline points="20 6 9 17 4 12" />
    </svg>
  );
}

export function LogLevelBadge({
  level,
  onRemove,
  fixedWidth = false,
}: {
  level: string;
  onRemove?: () => void;
  fixedWidth?: boolean;
}) {
  const normalized = level.toLowerCase();
  const color = LEVEL_COLORS[normalized] ?? "gray";

  return (
    <Badge
      size="xs"
      variant="light"
      color={color}
      pr={onRemove ? 3 : undefined}
      style={{
        ...(fixedWidth ? { minWidth: 52 } : {}),
        textTransform: "uppercase",
        flexShrink: 0,
      }}
      rightSection={
        onRemove ? (
          <CloseButton
            size="xs"
            variant="transparent"
            color={color}
            onMouseDown={(event) => event.preventDefault()}
            onClick={onRemove}
            aria-label={`Remove ${normalized}`}
          />
        ) : undefined
      }
    >
      {normalized}
    </Badge>
  );
}

export function LogLevelOptionRow({ level, checked }: { level: LogLevel; checked: boolean }) {
  return (
    <Group flex="1" gap="xs" wrap="nowrap">
      <LogLevelBadge level={level} />
      {checked ? (
        <span style={{ marginInlineStart: "auto", display: "flex" }}>
          <CheckIcon />
        </span>
      ) : null}
    </Group>
  );
}
