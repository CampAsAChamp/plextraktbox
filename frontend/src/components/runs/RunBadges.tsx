import { Badge } from "@mantine/core";
import type { SelectProps } from "@mantine/core";

export function runStatusColor(status: string) {
  if (status === "success") return "green";
  if (status === "failed") return "red";
  if (status === "partial") return "orange";
  return "gray";
}

export function runTriggerColor(trigger: string) {
  if (trigger === "scheduled") return "violet";
  if (trigger === "manual") return "teal";
  return "gray";
}

export function RunStatusBadge({ status }: { status: string }) {
  return (
    <Badge color={runStatusColor(status)} variant="light">
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

export const renderRunStatusOption: SelectProps["renderOption"] = ({ option }) => (
  <RunStatusBadge status={option.value} />
);

export const renderRunTriggerOption: SelectProps["renderOption"] = ({ option }) => (
  <RunTriggerBadge trigger={option.value} />
);
