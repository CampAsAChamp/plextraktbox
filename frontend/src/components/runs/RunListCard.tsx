import { Group, Paper, Stack, Text, UnstyledButton } from "@mantine/core";
import type { RunListItem } from "src/api/jobs";
import { useDisplayPreferences } from "src/settings/DisplayPreferencesProvider";
import { formatDateTime, formatDuration } from "src/utils/dateTimeFormat";
import { SourcePairLabel } from "src/components/services/SourcePairLabel";
import dryRunRowClasses from "../../styles/dryRunRow.module.css";
import { DryRunBadge, RunStatusBadge, RunTriggerBadge } from "src/components/runs/RunBadges";

type RunListCardProps = {
  run: RunListItem;
  onOpen: () => void;
};

function runDurationMs(run: RunListItem): number | null {
  if (!run.finished_at) return null;
  return new Date(run.finished_at).getTime() - new Date(run.started_at).getTime();
}

/** Mobile run card — tap opens run detail. */
export function RunListCard({ run, onOpen }: RunListCardProps) {
  const { preferences } = useDisplayPreferences();
  const durationMs = runDurationMs(run);
  const duration = durationMs === null ? "running…" : formatDuration(durationMs);

  return (
    <UnstyledButton
      onClick={onOpen}
      aria-label={`Run #${run.id} for ${run.job_name ?? `job #${run.job_id}`}`}
      style={{ display: "block", width: "100%", borderRadius: "var(--mantine-radius-lg)" }}
    >
      <Paper
        withBorder
        radius="lg"
        p="md"
        className={run.dry_run ? dryRunRowClasses.dryRunRow : undefined}
      >
        <Stack gap="sm">
          <Group justify="space-between" align="flex-start" wrap="wrap" gap="xs">
            <Text fw={600} size="md">
              Run #{run.id}
            </Text>
            <Group gap="xs" wrap="wrap">
              <RunStatusBadge status={run.status} />
              <DryRunBadge dryRun={run.dry_run} />
            </Group>
          </Group>
          <Text size="sm" style={{ wordBreak: "break-word" }}>
            {run.job_name ?? `Job #${run.job_id}`}
          </Text>
          {run.source_pair ? (
            <Stack gap={4}>
              <Text size="xs" c="dimmed" tt="uppercase" fw={600}>
                Job type
              </Text>
              <SourcePairLabel sourcePair={run.source_pair} variant="icons" />
            </Stack>
          ) : null}
          <Group gap="xs" wrap="wrap">
            <RunTriggerBadge trigger={run.trigger} />
            <Text size="xs" c="dimmed">
              {formatDateTime(run.started_at, preferences)}
            </Text>
            <Text size="xs" c="dimmed">
              · {duration}
            </Text>
          </Group>
        </Stack>
      </Paper>
    </UnstyledButton>
  );
}
