import { CloseButton, Group } from "@mantine/core"
import type { ReactNode } from "react"

import { type BadgeDisplayMode, ResponsiveBadge } from "src/components/badges/ResponsiveBadge"
import { CheckIcon } from "src/components/icons/CheckIcon"
import { ClockIcon } from "src/components/icons/ClockIcon"
import { DropletsIcon } from "src/components/icons/DropletsIcon"
import { MinusIcon } from "src/components/icons/MinusIcon"
import { SyncIcon } from "src/components/icons/SyncIcon"
import { UserIcon } from "src/components/icons/UserIcon"
import { WarningIcon } from "src/components/icons/WarningIcon"
import { XIcon } from "src/components/icons/XIcon"

function runStatusColor(status: string) {
  if (status === "success") return "green"
  if (status === "failed") return "red"
  if (status === "partial") return "orange"
  if (status === "running") return "blue"
  return "gray"
}

function runStatusIcon(status: string): ReactNode {
  if (status === "success") return <CheckIcon size={14} />
  if (status === "failed") return <XIcon size={14} />
  if (status === "partial") return <WarningIcon size={14} />
  if (status === "running") return <SyncIcon size={14} />
  return <MinusIcon size={14} />
}

function runTriggerColor(trigger: string) {
  if (trigger === "scheduled") return "violet"
  if (trigger === "manual") return "teal"
  return "gray"
}

function runTriggerIcon(trigger: string): ReactNode {
  if (trigger === "scheduled") return <ClockIcon size={14} />
  if (trigger === "manual") return <UserIcon size={14} />
  return <MinusIcon size={14} />
}

export function RunStatusBadge({
  status,
  onRemove,
  pulse = false,
  mode = "label",
}: {
  status: string
  onRemove?: () => void
  /** Breathing animation for live runs in the runs list — keep off in filters/chrome. */
  pulse?: boolean
  mode?: BadgeDisplayMode
}) {
  // Removable filter chips always need the label + close control.
  const displayMode = onRemove ? "label" : mode

  return (
    <ResponsiveBadge
      label={status}
      color={runStatusColor(status)}
      icon={runStatusIcon(status)}
      mode={displayMode}
      className={pulse && status === "running" ? "ptbPulseOpacity" : undefined}
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
    />
  )
}

export function RunTriggerBadge({ trigger, mode = "label" }: { trigger: string; mode?: BadgeDisplayMode }) {
  return <ResponsiveBadge label={trigger} color={runTriggerColor(trigger)} icon={runTriggerIcon(trigger)} mode={mode} />
}

export function DryRunBadge({ dryRun, compact = false, mode = "label" }: { dryRun: boolean; compact?: boolean; mode?: BadgeDisplayMode }) {
  if (compact) {
    return (
      <ResponsiveBadge
        label={dryRun ? "yes" : "no"}
        color={dryRun ? "blue" : "gray"}
        icon={dryRun ? <DropletsIcon size={14} /> : <MinusIcon size={14} />}
        mode={mode}
      />
    )
  }

  if (!dryRun) return null
  return <ResponsiveBadge label="dry run" color="blue" icon={<DropletsIcon size={14} />} mode={mode} />
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
  )
}
