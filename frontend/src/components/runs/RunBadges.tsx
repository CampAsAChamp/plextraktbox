import { Badge, CloseButton, Group } from "@mantine/core";
import type { SelectProps } from "@mantine/core";

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

export function runStatusColor(status: string) {
  if (status === "success") return "green";
  if (status === "failed") return "red";
  if (status === "partial") return "orange";
  if (status === "running") return "blue";
  return "gray";
}

export function runTriggerColor(trigger: string) {
  if (trigger === "scheduled") return "violet";
  if (trigger === "manual") return "teal";
  return "gray";
}

export function RunStatusBadge({ status, onRemove }: { status: string; onRemove?: () => void }) {
  return (
    <Badge
      color={runStatusColor(status)}
      variant="light"
      pr={onRemove ? 3 : undefined}
      rightSection={
        onRemove ? (
          <CloseButton
            size="xs"
            variant="transparent"
            color={runStatusColor(status)}
            onMouseDown={(event) => event.preventDefault()}
            onClick={onRemove}
            aria-label={`Remove ${status}`}
          />
        ) : undefined
      }
    >
      {status}
    </Badge>
  );
}

export function RunTriggerBadge({ trigger }: { trigger: string }) {
  return (
    <Badge color={runTriggerColor(trigger)} variant="light">
      {trigger}
    </Badge>
  );
}

export function DryRunBadge({ dryRun, compact = false }: { dryRun: boolean; compact?: boolean }) {
  if (compact) {
    return (
      <Badge color={dryRun ? "blue" : "gray"} variant="light">
        {dryRun ? "yes" : "no"}
      </Badge>
    );
  }

  if (!dryRun) return null;
  return (
    <Badge color="blue" variant="light">
      dry run
    </Badge>
  );
}

export function RunStatusOptionRow({ status, checked }: { status: string; checked: boolean }) {
  return (
    <Group flex="1" gap="xs" wrap="nowrap">
      <RunStatusBadge status={status} />
      {checked ? (
        <span style={{ marginInlineStart: "auto", display: "flex" }}>
          <CheckIcon />
        </span>
      ) : null}
    </Group>
  );
}

export const renderRunStatusOption: SelectProps["renderOption"] = ({ option, checked }) => (
  <RunStatusOptionRow status={option.value} checked={!!checked} />
);

export const renderRunTriggerOption: SelectProps["renderOption"] = ({ option }) => (
  <RunTriggerBadge trigger={option.value} />
);
