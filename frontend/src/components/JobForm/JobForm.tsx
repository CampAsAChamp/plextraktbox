import {
  Badge,
  Button,
  Checkbox,
  Group,
  Radio,
  Stack,
  Switch,
  Table,
  Text,
  TextInput,
} from "@mantine/core";
import { useDebouncedValue } from "@mantine/hooks";
import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { z } from "zod";
import type { DataType, Job, JobInput, NotifyMode, SourcePair } from "../../api/jobs";
import { DATA_TYPES_BY_PAIR, SOURCE_PAIR_LABELS } from "../../api/jobs";
import { previewSchedule } from "../../api/jobApi";
import { NOTIFY_MODE_LABELS } from "../../api/notifications";
import { useDisplayPreferences } from "../../settings/DisplayPreferencesProvider";
import { CRON_INVALID_MESSAGE, isValidCronExpression } from "../../utils/cron";
import { CRON_PRESETS, matchCronPreset } from "../../utils/cronPresets";
import { formatScheduleDateTimeParts } from "../../utils/dateTimeFormat";
import { DataTypeBadge } from "../services/DataTypeBadge";
import { SourcePairLabel } from "../services/SourcePairLabel";
import { SaveIcon } from "../icons/SaveIcon";

const jobSchema = z.object({
  name: z.string().min(1, "Name is required").max(120),
  source_pair: z.enum(["plex_trakt", "letterboxd_plex", "letterboxd_trakt"]),
  cron: z
    .string()
    .min(1, "Cron expression is required")
    .refine(isValidCronExpression, { message: CRON_INVALID_MESSAGE }),
  data_types: z.array(z.enum(["watchlist", "ratings", "watched"])).min(1, "Select at least one data type"),
});

interface JobFormProps {
  initial?: Job;
  loading?: boolean;
  onSubmit: (input: JobInput) => void;
  onCancel?: () => void;
}

const SOURCE_PAIRS = Object.keys(SOURCE_PAIR_LABELS) as SourcePair[];

export function JobForm({ initial, loading = false, onSubmit, onCancel }: JobFormProps) {
  const { preferences } = useDisplayPreferences();
  const [name, setName] = useState(initial?.name ?? "");
  const [sourcePair, setSourcePair] = useState<SourcePair>(initial?.source_pair ?? "plex_trakt");
  const [cron, setCron] = useState(initial?.cron ?? "0 3 * * *");
  const [enabled, setEnabled] = useState(initial?.enabled ?? true);
  const [dryRun, setDryRun] = useState(initial?.dry_run ?? false);
  const [notifyMode, setNotifyMode] = useState<NotifyMode>(initial?.notify_mode ?? "inherit");
  const [dataTypes, setDataTypes] = useState<DataType[]>(
    initial?.data_types ?? DATA_TYPES_BY_PAIR.plex_trakt,
  );
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [debouncedCron] = useDebouncedValue(cron, 300);
  const cronValid = isValidCronExpression(debouncedCron);
  const activePreset = matchCronPreset(cron);

  const previewQuery = useQuery({
    queryKey: ["schedule-preview", debouncedCron],
    queryFn: () => previewSchedule(debouncedCron.trim(), 5),
    enabled: cronValid,
    staleTime: 30_000,
  });

  useEffect(() => {
    if (initial) return;
    const allowed = DATA_TYPES_BY_PAIR[sourcePair];
    setDataTypes((current) => current.filter((dt) => allowed.includes(dt)));
  }, [sourcePair, initial]);

  function toggleDataType(dataType: DataType) {
    setDataTypes((current) =>
      current.includes(dataType)
        ? current.filter((item) => item !== dataType)
        : [...current, dataType],
    );
  }

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    const parsed = jobSchema.safeParse({
      name,
      source_pair: sourcePair,
      cron,
      data_types: dataTypes,
    });
    if (!parsed.success) {
      const fieldErrors: Record<string, string> = {};
      for (const issue of parsed.error.issues) {
        const key = String(issue.path[0] ?? "form");
        fieldErrors[key] = issue.message;
      }
      setErrors(fieldErrors);
      return;
    }
    setErrors({});
    onSubmit({
      name,
      source_pair: sourcePair,
      enabled,
      cron,
      dry_run: dryRun,
      data_types: dataTypes,
      notify_mode: notifyMode,
    });
  }

  const allowedDataTypes = DATA_TYPES_BY_PAIR[sourcePair];

  return (
    <form onSubmit={handleSubmit}>
      <Stack gap="md">
        <TextInput
          label="Name"
          value={name}
          onChange={(event) => setName(event.currentTarget.value)}
          error={errors.name}
          required
        />

        <Radio.Group
          label="Job Type"
          value={sourcePair}
          onChange={(value) => setSourcePair(value as SourcePair)}
        >
          <Stack gap="xs" mt="xs">
            {SOURCE_PAIRS.map((pair) => (
              <Radio
                key={pair}
                value={pair}
                label={<SourcePairLabel sourcePair={pair} variant="logo" logoSize={24} />}
              />
            ))}
          </Stack>
        </Radio.Group>

        <Stack gap="xs">
          <Text size="sm" fw={500}>
            Data types
          </Text>
          {allowedDataTypes.map((dataType) => (
            <Checkbox
              key={dataType}
              label={<DataTypeBadge dataType={dataType} />}
              checked={dataTypes.includes(dataType)}
              onChange={() => toggleDataType(dataType)}
            />
          ))}
          {sourcePair === "plex_trakt" ? (
            <Text size="xs" c="dimmed">
              TV shows and episodes sync when show libraries are selected under Connections.
            </Text>
          ) : null}
          {errors.data_types ? (
            <Text size="sm" c="red">
              {errors.data_types}
            </Text>
          ) : null}
        </Stack>

        <Stack gap="xs">
          <Text size="sm" fw={500}>
            Schedule
          </Text>
          <Group gap="xs">
            {CRON_PRESETS.map((preset) => (
              <Button
                key={preset.id}
                type="button"
                size="xs"
                variant={activePreset === preset.id ? "filled" : "light"}
                onClick={() => setCron(preset.cron)}
              >
                {preset.label}
              </Button>
            ))}
          </Group>
          {activePreset ? (
            <Text size="xs" c="dimmed">
              {CRON_PRESETS.find((preset) => preset.id === activePreset)?.description}
            </Text>
          ) : null}
          <TextInput
            label="Cron expression"
            description={
              <>
                UTC cron (minute hour day month weekday). Weekday uses 0=Monday … 6=Sunday. Use{" "}
                <a href="https://crontab.guru/" target="_blank" rel="noreferrer">
                  crontab.guru
                </a>{" "}
                carefully — it numbers Sunday as 0.
              </>
            }
            value={cron}
            onChange={(event) => setCron(event.currentTarget.value)}
            error={errors.cron}
            required
          />
          {cronValid ? (
            <Stack gap={4}>
              <Text size="sm" fw={500}>
                Next 5 runs
              </Text>
              {previewQuery.isLoading ? (
                <Text size="sm" c="dimmed">
                  Calculating…
                </Text>
              ) : previewQuery.isError ? (
                <Text size="sm" c="red">
                  Could not preview schedule.
                </Text>
              ) : (
                <Table
                  withTableBorder
                  withColumnBorders
                  horizontalSpacing="sm"
                  verticalSpacing={4}
                  style={{ width: "fit-content" }}
                >
                  <Table.Thead>
                    <Table.Tr>
                      <Table.Th>Day</Table.Th>
                      <Table.Th>Date</Table.Th>
                      <Table.Th>Time</Table.Th>
                    </Table.Tr>
                  </Table.Thead>
                  <Table.Tbody>
                    {(previewQuery.data?.times ?? []).map((time) => {
                      const parts = formatScheduleDateTimeParts(time, preferences);
                      return (
                        <Table.Tr key={time}>
                          <Table.Td>{parts.weekday}</Table.Td>
                          <Table.Td>{parts.date}</Table.Td>
                          <Table.Td>{parts.time}</Table.Td>
                        </Table.Tr>
                      );
                    })}
                  </Table.Tbody>
                </Table>
              )}
              <Text size="xs" c="dimmed">
                Times shown in your display timezone; the schedule itself runs in UTC.
              </Text>
            </Stack>
          ) : null}
        </Stack>

        <Group>
          <Switch label="Enabled" checked={enabled} onChange={(event) => setEnabled(event.currentTarget.checked)} />
          <Switch
            label="Dry run"
            description="Log planned changes without writing"
            checked={dryRun}
            onChange={(event) => setDryRun(event.currentTarget.checked)}
          />
        </Group>

        <Radio.Group
          label="Notifications"
          description="Control whether this job sends alerts when runs finish"
          value={notifyMode}
          onChange={(value) => setNotifyMode(value as NotifyMode)}
        >
          <Stack gap="xs" mt="xs">
            {(Object.keys(NOTIFY_MODE_LABELS) as NotifyMode[]).map((mode) => (
              <Radio key={mode} value={mode} label={NOTIFY_MODE_LABELS[mode]} />
            ))}
          </Stack>
        </Radio.Group>

        <Group>
          <Button type="submit" loading={loading} leftSection={<SaveIcon />}>
            Save job
          </Button>
          {onCancel ? (
            <Button type="button" variant="subtle" color="red" onClick={onCancel}>
              Cancel
            </Button>
          ) : null}
        </Group>
      </Stack>
    </form>
  );
}

export function JobStatusBadge({ enabled }: { enabled: boolean }) {
  return (
    <Badge color={enabled ? "green" : "gray"} variant="light">
      {enabled ? "Enabled" : "Disabled"}
    </Badge>
  );
}

export { DryRunBadge } from "../runs/RunBadges";
