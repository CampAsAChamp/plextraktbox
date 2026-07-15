import { Alert, Button, Group, Loader, SimpleGrid, Stack, Text, Title, Tooltip } from "@mantine/core";
import { notifications } from "@mantine/notifications";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useLocation, useParams } from "react-router-dom";
import { ApiError } from "../api/client";
import { getRun, markRunFailed } from "../api/runs";
import { HelpCircleIcon } from "../components/icons/HelpCircleIcon";
import { LogViewer } from "../components/LogViewer/LogViewer";
import { useDisplayPreferences } from "../settings/DisplayPreferencesProvider";
import { formatDateTime } from "../utils/dateTimeFormat";
import { DryRunBadge, RunStatusBadge, RunTriggerBadge } from "../components/runs/RunBadges";
import { UnmatchedItemsSection } from "../components/runs/UnmatchedItemsSection";
import { SourcePairLabel } from "../components/services/SourcePairLabel";

const SUMMARY_LABELS: Record<string, string> = {
  matched: "Matched",
  planned: "Planned",
  added: "Added",
  removed: "Removed",
  rated: "Rated",
  watched: "Watched",
  skipped: "Skipped",
  errors: "Errors",
  unmatched_count: "Unmatched",
};

const SUMMARY_TOOLTIPS: Record<string, string> = {
  matched: "Items matched across services that need a rating or watched update.",
  planned: "Total changes planned for this run (add, remove, or update).",
  added: "Watchlist items added to Trakt to match your Plex watchlist.",
  removed: "Watchlist items removed from Trakt to match your Plex watchlist.",
  rated: "Ratings synced from Letterboxd to Plex and Trakt.",
  watched: "Items marked as watched in Plex based on your Trakt history.",
  skipped: "Planned changes skipped because they were already applied or not needed.",
  errors: "Planned changes that failed during apply.",
  unmatched_count:
    "Items that could not be matched across services or are missing TMDB/IMDb IDs.",
};

export function RunDetailPage() {
  const { runId } = useParams();
  const location = useLocation();
  const queryClient = useQueryClient();
  const id = Number(runId);
  const { preferences } = useDisplayPreferences();
  const backTo =
    typeof (location.state as { from?: unknown } | null)?.from === "string"
      ? (location.state as { from: string }).from
      : "/runs";

  const runQuery = useQuery({
    queryKey: ["runs", id],
    queryFn: () => getRun(id),
    enabled: Number.isFinite(id),
    refetchInterval: (query) => (query.state.data?.status === "running" ? 2000 : false),
  });

  const markFailedMutation = useMutation({
    mutationFn: () => markRunFailed(id),
    onSuccess: (run) => {
      queryClient.setQueryData(["runs", id], run);
      void queryClient.invalidateQueries({ queryKey: ["runs"] });
      notifications.show({ color: "orange", message: `Run #${run.id} marked as failed` });
    },
    onError: (error: unknown) => {
      const message = error instanceof ApiError ? String(error.message) : "Could not mark run as failed";
      notifications.show({ color: "red", message });
    },
  });

  if (!Number.isFinite(id)) {
    return <Text c="red">Invalid run id.</Text>;
  }

  if (runQuery.isLoading) {
    return (
      <Group>
        <Loader size="sm" />
        <Text>Loading run…</Text>
      </Group>
    );
  }

  if (runQuery.isError || !runQuery.data) {
    return <Text c="red">Run not found.</Text>;
  }

  const run = runQuery.data;

  return (
    <Stack gap="md">
      <Stack gap="xs">
        <Button component={Link} to={backTo} variant="subtle" w="fit-content">
          Back to run history
        </Button>
        <Group justify="space-between">
          <Title order={3}>Run #{run.id}</Title>
          <Group gap="sm">
            {run.status === "running" ? (
              <Button
                color="red"
                variant="light"
                loading={markFailedMutation.isPending}
                onClick={() => {
                  if (
                    window.confirm(
                      "Mark this run as failed? If sync work is still in progress on the server, it may continue until it finishes, but this run will stay marked failed.",
                    )
                  ) {
                    markFailedMutation.mutate();
                  }
                }}
              >
                Mark as failed
              </Button>
            ) : null}
            <Button component={Link} to={`/runs?job_id=${run.job_id}`} variant="light">
              Job history
            </Button>
          </Group>
        </Group>
      </Stack>

      <Group gap="sm">
        <RunStatusBadge status={run.status} />
        <RunTriggerBadge trigger={run.trigger} />
        <DryRunBadge dryRun={run.dry_run} />
      </Group>

      <Stack gap={4}>
        <Text>
          <strong>Job:</strong> {run.job_name ?? `#${run.job_id}`}
        </Text>
        <Group gap="xs" align="center">
          <Text>
            <strong>Job Type:</strong>
          </Text>
          {run.source_pair ? (
            <SourcePairLabel sourcePair={run.source_pair} variant="icons" />
          ) : (
            <Text c="dimmed">—</Text>
          )}
        </Group>
        <Text>
          <strong>Started:</strong> {formatDateTime(run.started_at, preferences)}
        </Text>
        <Text>
          <strong>Finished:</strong> {formatDateTime(run.finished_at, preferences)}
        </Text>
      </Stack>

      {run.error ? (
        <Alert color="red" title="Error">
          {run.error}
        </Alert>
      ) : null}

      <Stack gap="xs">
        <Text fw={500}>Summary</Text>
        <SimpleGrid cols={{ base: 2, sm: 4 }}>
          {Object.entries(run.summary)
            .filter(([key]) => key !== "unmatched")
            .map(([key, value]) => (
            <Stack key={key} gap={0}>
              <Tooltip
                label={SUMMARY_TOOLTIPS[key] ?? SUMMARY_LABELS[key] ?? key}
                multiline
                w={260}
                openDelay={500}
              >
                <Group
                  gap={4}
                  wrap="nowrap"
                  c="dimmed"
                  style={{ cursor: "help", width: "fit-content" }}
                >
                  <Text size="xs" c="inherit">
                    {SUMMARY_LABELS[key] ?? key}
                  </Text>
                  <HelpCircleIcon size={12} />
                </Group>
              </Tooltip>
              <Text fw={600}>{typeof value === "number" ? value : "—"}</Text>
            </Stack>
          ))}
        </SimpleGrid>
      </Stack>

      <UnmatchedItemsSection items={run.summary.unmatched} />

      <Stack gap="xs">
        <Text fw={500}>Logs</Text>
        <LogViewer runId={run.id} isLive={run.status === "running"} />
      </Stack>
    </Stack>
  );
}
