import { ActionIcon, Group, Tooltip } from "@mantine/core"
import type { ReactNode } from "react"
import { Link } from "react-router-dom"

import type { Job } from "src/api/jobs"
import { PencilIcon } from "src/components/icons/PencilIcon"
import { TrashIcon } from "src/components/icons/TrashIcon"
import type { RunMode } from "src/hooks/useRunJob"

function StrokeIcon({ size = 14, children }: { size?: number; children: ReactNode }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden
    >
      {children}
    </svg>
  )
}

export function HistoryIcon() {
  return (
    <StrokeIcon>
      <path d="M12 8v4l3 3" />
      <path d="M3.05 11a9 9 0 1 1 .5 4" />
      <path d="M3 4v5h5" />
    </StrokeIcon>
  )
}

export function CloneIcon() {
  return (
    <StrokeIcon>
      <rect x="9" y="9" width="13" height="13" rx="2" />
      <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
    </StrokeIcon>
  )
}

export type JobActionsProps = {
  job: Job
  isRunning: (job: Job, mode: RunMode) => boolean
  onRun: (job: Job, mode: RunMode) => void
  onClone?: (job: Job) => void
  clonePending?: boolean
  onDelete?: (job: Job) => void
  showHistory?: boolean
  showEdit?: boolean
}

export function JobActions({
  job,
  isRunning,
  onRun,
  onClone,
  clonePending = false,
  onDelete,
  showHistory = true,
  showEdit = true,
}: JobActionsProps) {
  return (
    <Group gap={4} wrap="wrap">
      <Tooltip label="Run now">
        <ActionIcon variant="light" aria-label={`Run ${job.name}`} loading={isRunning(job, "run")} onClick={() => onRun(job, "run")}>
          ▶
        </ActionIcon>
      </Tooltip>
      <Tooltip label="Dry-run">
        <ActionIcon
          variant="light"
          color="blue"
          aria-label={`Dry-run ${job.name}`}
          loading={isRunning(job, "dry-run")}
          onClick={() => onRun(job, "dry-run")}
        >
          ▷
        </ActionIcon>
      </Tooltip>
      {showEdit ? (
        <Tooltip label="Edit">
          <ActionIcon component={Link} to={`/jobs/${job.id}/edit`} variant="subtle" aria-label={`Edit ${job.name}`}>
            <PencilIcon />
          </ActionIcon>
        </Tooltip>
      ) : null}
      {onClone ? (
        <Tooltip label="Clone">
          <ActionIcon variant="subtle" aria-label={`Clone ${job.name}`} loading={clonePending} onClick={() => onClone(job)}>
            <CloneIcon />
          </ActionIcon>
        </Tooltip>
      ) : null}
      {showHistory ? (
        <Tooltip label="History">
          <ActionIcon component={Link} to={`/runs?job_id=${job.id}`} variant="subtle" aria-label={`History for ${job.name}`}>
            <HistoryIcon />
          </ActionIcon>
        </Tooltip>
      ) : null}
      {onDelete ? (
        <Tooltip label="Delete">
          <ActionIcon color="red" variant="subtle" aria-label={`Delete ${job.name}`} onClick={() => onDelete(job)}>
            <TrashIcon />
          </ActionIcon>
        </Tooltip>
      ) : null}
    </Group>
  )
}
