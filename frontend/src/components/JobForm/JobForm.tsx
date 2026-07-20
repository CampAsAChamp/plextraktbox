import {
  Accordion,
  Badge,
  Box,
  Button,
  Checkbox,
  Group,
  Radio,
  SimpleGrid,
  Stack,
  Switch,
  Table,
  Text,
  Textarea,
  TextInput,
  Tooltip,
} from "@mantine/core"
import { useDebouncedValue } from "@mantine/hooks"
import { useQuery } from "@tanstack/react-query"
import { useEffect, useRef, useState } from "react"
import { z } from "zod"

import { previewSchedule } from "src/api/jobApi"
import type { DataType, Job, JobInput, NotifyMode, SourcePair } from "src/api/jobs"
import { DATA_TYPES_BY_PAIR, SOURCE_PAIR_LABELS } from "src/api/jobs"
import { NOTIFY_MODE_LABELS } from "src/api/notifications"
import { formatExcludeLines, getSettings, parseExcludeLines } from "src/api/settings"
import { type BadgeDisplayMode, ResponsiveBadge } from "src/components/badges/ResponsiveBadge"
import { CheckIcon } from "src/components/icons/CheckIcon"
import { HelpCircleIcon } from "src/components/icons/HelpCircleIcon"
import { SaveIcon } from "src/components/icons/SaveIcon"
import { XIcon } from "src/components/icons/XIcon"
import { JobFormMobileNav, JobFormSectionTitle, JobFormToc } from "src/components/JobForm/JobFormToc"
import { DataTypeBadge } from "src/components/services/DataTypeBadge"
import { SourcePairLabel } from "src/components/services/SourcePairLabel"
import { SourceOfTruthCallout } from "src/components/sync/SourceOfTruthCallout"
import { RoundedTable } from "src/components/table/RoundedTable"
import { formatTimezoneLabel } from "src/settings/displayPreferences"
import { useDisplayPreferences } from "src/settings/DisplayPreferencesProvider"
import { CRON_INVALID_MESSAGE, isValidCronExpression } from "src/utils/cron"
import { CRON_PRESETS, matchCronPreset } from "src/utils/cronPresets"
import { formatScheduleDateTimeParts } from "src/utils/dateTimeFormat"

const SECTION_SCROLL_STYLE = { scrollMarginTop: 80 } as const

const jobSchema = z.object({
  name: z.string().min(1, "Name is required").max(120),
  source_pair: z.enum(["plex_trakt", "letterboxd_plex", "letterboxd_trakt"]),
  cron: z.string().min(1, "Cron expression is required").refine(isValidCronExpression, { message: CRON_INVALID_MESSAGE }),
  data_types: z.array(z.enum(["watchlist", "ratings", "watched"])).min(1, "Select at least one data type"),
})

interface JobFormProps {
  initial?: Job
  loading?: boolean
  onSubmit: (input: JobInput) => void
  onCancel?: () => void
}

const SOURCE_PAIRS = Object.keys(SOURCE_PAIR_LABELS) as SourcePair[]

export function JobForm({ initial, loading = false, onSubmit, onCancel }: JobFormProps) {
  const { preferences } = useDisplayPreferences()
  const [name, setName] = useState(initial?.name ?? "")
  const [sourcePair, setSourcePair] = useState<SourcePair>(initial?.source_pair ?? "plex_trakt")
  const [cron, setCron] = useState(initial?.cron ?? "0 3 * * *")
  const [enabled, setEnabled] = useState(initial?.enabled ?? true)
  const [dryRun, setDryRun] = useState(initial?.dry_run ?? false)
  const [requireDryRunFirst, setRequireDryRunFirst] = useState(initial?.require_dry_run_first ?? true)
  const [notifyMode, setNotifyMode] = useState<NotifyMode>(initial?.notify_mode ?? "inherit")
  const [dataTypes, setDataTypes] = useState<DataType[]>(initial?.data_types ?? DATA_TYPES_BY_PAIR.plex_trakt)
  const [excludeTmdb, setExcludeTmdb] = useState(formatExcludeLines(initial?.exclude_ids?.tmdb))
  const [excludeImdb, setExcludeImdb] = useState(formatExcludeLines(initial?.exclude_ids?.imdb))
  const [excludeTvdb, setExcludeTvdb] = useState(formatExcludeLines(initial?.exclude_ids?.tvdb))
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [debouncedCron] = useDebouncedValue(cron, 300)
  const cronValid = isValidCronExpression(debouncedCron)
  const cronInputRef = useRef<HTMLInputElement>(null)
  const [scheduleSelection, setScheduleSelection] = useState<string>(() => matchCronPreset(initial?.cron ?? "0 3 * * *") ?? "custom")
  const [defaultsApplied, setDefaultsApplied] = useState(Boolean(initial))
  const isCustomSchedule = scheduleSelection === "custom"
  const activePreset = isCustomSchedule ? null : scheduleSelection

  const settingsQuery = useQuery({
    queryKey: ["settings"],
    queryFn: getSettings,
  })
  const cronTimezoneResolved = settingsQuery.data?.cron_timezone_resolved ?? "UTC"
  const cronTimezoneLabel = cronTimezoneResolved === "UTC" ? "UTC" : formatTimezoneLabel(cronTimezoneResolved)

  const previewQuery = useQuery({
    queryKey: ["schedule-preview", debouncedCron, cronTimezoneResolved],
    queryFn: () => previewSchedule(debouncedCron.trim(), 5),
    enabled: cronValid,
    staleTime: 30_000,
  })

  useEffect(() => {
    if (initial || defaultsApplied || !settingsQuery.data) return
    setCron(settingsQuery.data.default_cron)
    setScheduleSelection(matchCronPreset(settingsQuery.data.default_cron) ?? "custom")
    setDryRun(settingsQuery.data.global_dry_run)
    setDefaultsApplied(true)
  }, [initial, defaultsApplied, settingsQuery.data])

  useEffect(() => {
    const allowed = DATA_TYPES_BY_PAIR[sourcePair]
    setDataTypes((current) => {
      const next = current.filter((dt) => allowed.includes(dt))
      // Drop types that don't apply to the new job type (e.g. Watched on Letterboxd → Plex).
      // If none remain, select all allowed defaults so save isn't blocked with a hidden mismatch.
      return next.length > 0 ? next : [...allowed]
    })
  }, [sourcePair])

  function toggleDataType(dataType: DataType) {
    setDataTypes((current) => (current.includes(dataType) ? current.filter((item) => item !== dataType) : [...current, dataType]))
  }

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault()
    const parsed = jobSchema.safeParse({
      name,
      source_pair: sourcePair,
      cron,
      data_types: dataTypes,
    })
    if (!parsed.success) {
      const fieldErrors: Record<string, string> = {}
      for (const issue of parsed.error.issues) {
        const key = String(issue.path[0] ?? "form")
        fieldErrors[key] = issue.message
      }
      setErrors(fieldErrors)
      return
    }
    setErrors({})
    onSubmit({
      name,
      source_pair: sourcePair,
      enabled,
      cron,
      dry_run: dryRun,
      require_dry_run_first: requireDryRunFirst,
      data_types: dataTypes,
      notify_mode: notifyMode,
      exclude_ids: {
        tmdb: parseExcludeLines(excludeTmdb),
        imdb: parseExcludeLines(excludeImdb),
        tvdb: parseExcludeLines(excludeTvdb),
      },
    })
  }

  const allowedDataTypes = DATA_TYPES_BY_PAIR[sourcePair]
  const excludeCount = parseExcludeLines(excludeTmdb).length + parseExcludeLines(excludeImdb).length + parseExcludeLines(excludeTvdb).length

  return (
    <form onSubmit={handleSubmit}>
      <Stack gap="md">
        <JobFormMobileNav />
        <Group align="flex-start" gap="xl" wrap="nowrap">
          <JobFormToc />
          <Stack gap="xl" style={{ flex: 1, minWidth: 0 }}>
            <Box id="job-name" data-job-section="Name" style={SECTION_SCROLL_STYLE}>
              <TextInput
                label={<JobFormSectionTitle sectionId="job-name" />}
                value={name}
                onChange={(event) => setName(event.currentTarget.value)}
                error={errors.name}
                required
              />
            </Box>

            <Box id="job-type" data-job-section="Job Type" style={SECTION_SCROLL_STYLE}>
              <Radio.Group
                label={<JobFormSectionTitle sectionId="job-type" />}
                value={sourcePair}
                onChange={(value) => setSourcePair(value as SourcePair)}
              >
                <Stack gap="xs" mt="xs">
                  {SOURCE_PAIRS.map((pair) => (
                    <Radio key={pair} value={pair} label={<SourcePairLabel sourcePair={pair} variant="logo" logoSize={24} />} />
                  ))}
                </Stack>
              </Radio.Group>
            </Box>

            <Stack id="job-data-types" gap="xs" data-job-section="Data types" style={SECTION_SCROLL_STYLE}>
              <Text size="sm" fw={500}>
                <JobFormSectionTitle sectionId="job-data-types" />
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

            <SourceOfTruthCallout relevantTypes={allowedDataTypes} />

            <Stack id="job-schedule" gap="xs" data-job-section="Schedule" style={SECTION_SCROLL_STYLE}>
              <Text size="sm" fw={500}>
                <JobFormSectionTitle sectionId="job-schedule" />
              </Text>
              <SimpleGrid cols={{ base: 2, sm: 3, md: 4 }} spacing="xs">
                {CRON_PRESETS.map((preset) => (
                  <Button
                    key={preset.id}
                    type="button"
                    size="xs"
                    variant={scheduleSelection === preset.id ? "filled" : "light"}
                    onClick={() => {
                      setCron(preset.cron)
                      setScheduleSelection(preset.id)
                    }}
                  >
                    {preset.label}
                  </Button>
                ))}
                <Button
                  type="button"
                  size="xs"
                  variant={isCustomSchedule ? "filled" : "light"}
                  onClick={() => {
                    setScheduleSelection("custom")
                    cronInputRef.current?.focus()
                    cronInputRef.current?.select()
                  }}
                >
                  Custom
                </Button>
              </SimpleGrid>
              {activePreset ? (
                <Text size="xs" c="dimmed">
                  {CRON_PRESETS.find((preset) => preset.id === activePreset)?.description} ({cronTimezoneLabel})
                </Text>
              ) : (
                <Text size="xs" c="dimmed">
                  Edit the cron expression below ({cronTimezoneLabel})
                </Text>
              )}
              <TextInput
                ref={cronInputRef}
                label="Cron expression"
                description={
                  <>
                    Cron in {cronTimezoneLabel} (minute hour day month weekday). Weekday uses 0=Monday … 6=Sunday. Use{" "}
                    <a href="https://crontab.guru/" target="_blank" rel="noreferrer">
                      crontab.guru
                    </a>{" "}
                    carefully — it numbers Sunday as 0. Change the cron timezone under Settings.
                  </>
                }
                value={cron}
                onChange={(event) => {
                  const next = event.currentTarget.value
                  setCron(next)
                  setScheduleSelection(matchCronPreset(next) ?? "custom")
                }}
                error={errors.cron}
                required
                styles={{ input: { fontFamily: "var(--mantine-font-family-monospace)" } }}
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
                    <RoundedTable fitContent withColumnBorders horizontalSpacing="sm" verticalSpacing={4}>
                      <Table.Thead>
                        <Table.Tr>
                          <Table.Th>Day</Table.Th>
                          <Table.Th>Date</Table.Th>
                          <Table.Th>Time</Table.Th>
                        </Table.Tr>
                      </Table.Thead>
                      <Table.Tbody>
                        {(previewQuery.data?.times ?? []).map((time) => {
                          const parts = formatScheduleDateTimeParts(time, preferences)
                          return (
                            <Table.Tr key={time}>
                              <Table.Td>{parts.weekday}</Table.Td>
                              <Table.Td>{parts.date}</Table.Td>
                              <Table.Td>{parts.time}</Table.Td>
                            </Table.Tr>
                          )
                        })}
                      </Table.Tbody>
                    </RoundedTable>
                  )}
                  <Text size="xs" c="dimmed">
                    Times shown in your display timezone; the schedule itself runs in {cronTimezoneLabel}.
                  </Text>
                </Stack>
              ) : null}
            </Stack>

            <Stack id="job-options" gap="sm" data-job-section="Options" style={SECTION_SCROLL_STYLE}>
              <Text size="sm" fw={500}>
                <JobFormSectionTitle sectionId="job-options" />
              </Text>
              <Switch label="Enabled" checked={enabled} onChange={(event) => setEnabled(event.currentTarget.checked)} />
              <Switch
                label={
                  <Group gap={4} wrap="nowrap" component="span">
                    Dry run
                    <Tooltip label="Log planned changes without writing" withArrow openDelay={200}>
                      <Text component="span" c="dimmed" display="inline-flex" style={{ cursor: "help" }} aria-label="Dry run help">
                        <HelpCircleIcon size={12} />
                      </Text>
                    </Tooltip>
                  </Group>
                }
                checked={dryRun}
                onChange={(event) => setDryRun(event.currentTarget.checked)}
              />
              <Switch
                label={
                  <Group gap={4} wrap="nowrap" component="span">
                    Require dry-run first
                    <Tooltip label="Block live applies until this job has at least one successful dry-run" withArrow openDelay={200}>
                      <Text
                        component="span"
                        c="dimmed"
                        display="inline-flex"
                        style={{ cursor: "help" }}
                        aria-label="Require dry-run first help"
                      >
                        <HelpCircleIcon size={12} />
                      </Text>
                    </Tooltip>
                  </Group>
                }
                checked={requireDryRunFirst}
                onChange={(event) => setRequireDryRunFirst(event.currentTarget.checked)}
              />
            </Stack>

            <Accordion
              id="job-excludes"
              data-job-section="Exclude ids"
              variant="contained"
              chevronPosition="left"
              style={SECTION_SCROLL_STYLE}
            >
              <Accordion.Item value="excludes">
                <Accordion.Control>
                  <Group gap="sm">
                    <Text fw={500}>
                      <JobFormSectionTitle sectionId="job-excludes">Per-job exclude ids</JobFormSectionTitle>
                    </Text>
                    {excludeCount > 0 ? (
                      <Badge variant="light" size="sm">
                        {excludeCount}
                      </Badge>
                    ) : null}
                  </Group>
                </Accordion.Control>
                <Accordion.Panel>
                  <Stack gap="xs">
                    <Text size="xs" c="dimmed">
                      Merged with the global exclude list from Settings. One id per line.
                    </Text>
                    <Textarea
                      label="TMDB"
                      minRows={2}
                      value={excludeTmdb}
                      onChange={(event) => setExcludeTmdb(event.currentTarget.value)}
                    />
                    <Textarea
                      label="IMDb"
                      minRows={2}
                      value={excludeImdb}
                      onChange={(event) => setExcludeImdb(event.currentTarget.value)}
                    />
                    <Textarea
                      label="TVDB"
                      minRows={2}
                      value={excludeTvdb}
                      onChange={(event) => setExcludeTvdb(event.currentTarget.value)}
                    />
                  </Stack>
                </Accordion.Panel>
              </Accordion.Item>
            </Accordion>

            <Box id="job-notifications" data-job-section="Notifications" style={SECTION_SCROLL_STYLE}>
              <Radio.Group
                label={<JobFormSectionTitle sectionId="job-notifications" />}
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
            </Box>

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
        </Group>
      </Stack>
    </form>
  )
}

export function JobStatusBadge({ enabled, mode = "label" }: { enabled: boolean; mode?: BadgeDisplayMode }) {
  return (
    <ResponsiveBadge
      label={enabled ? "Enabled" : "Disabled"}
      color={enabled ? "green" : "red"}
      icon={enabled ? <CheckIcon size={14} /> : <XIcon size={14} />}
      mode={mode}
    />
  )
}

export { DryRunBadge } from "src/components/runs/RunBadges"
