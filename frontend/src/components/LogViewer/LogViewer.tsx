import { ActionIcon, Box, Button, Group, ScrollArea, Stack, Text, TextInput } from "@mantine/core"
import { useQuery } from "@tanstack/react-query"
import { useVirtualizer } from "@tanstack/react-virtual"
import { useCallback, useEffect, useMemo, useRef, useState } from "react"

import { listRunLogs, type LogEntry } from "src/api/logs"
import { ColoredJson, ColoredJsonSpans, JSON_SYNTAX_COLORS } from "src/components/LogViewer/ColoredJson"
import { LiveStreamAccent, LiveStreamIndicator } from "src/components/LogViewer/LiveStreamIndicator"
import {
  estimateLogLineHeight,
  formatContextValue,
  formatContextValueCompact,
  formatLogDisplayMessage,
  hasExpandableContext,
  LOG_LOGGER_BRACKET_COLOR,
  LOG_LOGGER_NAME_COLOR,
  logContextForDisplay,
  shouldPrettyPrintContextValue,
  shouldRenderStatusBadge,
  shouldSyntaxHighlightContextValue,
} from "src/components/LogViewer/logFormat"
import { LogLevelMultiSelect } from "src/components/LogViewer/LogLevelMultiSelect"
import { type LogLevel, LogLevelBadge } from "src/components/LogViewer/logLevels"
import { useLogStream } from "src/components/LogViewer/useLogStream"
import { RunStatusBadge } from "src/components/runs/RunBadges"
import { useDisplayPreferences } from "src/settings/DisplayPreferencesProvider"
import { TimezonePreferenceControls } from "src/settings/TimezonePreferenceControls"
import { formatTimestamp } from "src/utils/dateTimeFormat"

type LogViewerProps = {
  runId: number
  isLive: boolean
}

function LogLoggerLabel({ logger }: { logger: string }) {
  return (
    <Box component="span" visibleFrom="sm" style={{ minWidth: 120, flexShrink: 0 }}>
      <Box component="span" style={{ color: LOG_LOGGER_BRACKET_COLOR }}>
        [
      </Box>
      <Box component="span" style={{ color: LOG_LOGGER_NAME_COLOR }}>
        {logger}
      </Box>
      <Box component="span" style={{ color: LOG_LOGGER_BRACKET_COLOR }}>
        ]
      </Box>
    </Box>
  )
}

function InlineContextValue({ value }: { value: unknown }) {
  const compact = formatContextValueCompact(value)
  if (shouldSyntaxHighlightContextValue(value)) {
    return <ColoredJsonSpans value={compact} />
  }

  return (
    <Box component="span" style={{ color: JSON_SYNTAX_COLORS.string }}>
      {compact}
    </Box>
  )
}

function LogContextInline({ context }: { context: Record<string, unknown> }) {
  const entries = Object.entries(context)
  if (entries.length === 0) return null

  return (
    <>
      {entries.map(([key, value]) => {
        if (shouldRenderStatusBadge(key, value)) {
          return (
            <Box
              key={key}
              component="span"
              ml={8}
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: 4,
                verticalAlign: "middle",
              }}
            >
              <Text span size="xs" c="dimmed">
                {key}
              </Text>
              <RunStatusBadge status={value} />
            </Box>
          )
        }

        return (
          <Box key={key} component="span" ml={8} style={{ display: "inline", whiteSpace: "nowrap" }}>
            <Text span size="xs" c="dimmed">
              {key}=
            </Text>
            <Text span size="xs">
              <InlineContextValue value={value} />
            </Text>
          </Box>
        )
      })}
    </>
  )
}

function LogContextExpanded({ context }: { context: Record<string, unknown> }) {
  const entries = Object.entries(context)
  if (entries.length === 0) return null

  return (
    <Stack gap={6} mt={6} pl={4}>
      {entries.map(([key, value]) => {
        const formatted = formatContextValue(value)
        if (shouldRenderStatusBadge(key, value)) {
          return (
            <Group key={key} gap={6} wrap="nowrap" align="center">
              <Text size="xs" c="dimmed">
                {key}
              </Text>
              <RunStatusBadge status={value} />
            </Group>
          )
        }

        if (!shouldPrettyPrintContextValue(value)) {
          return (
            <Text key={key} size="xs">
              <Text span size="xs" c="dimmed">
                {key}=
              </Text>
              <InlineContextValue value={value} />
            </Text>
          )
        }

        return (
          <Box key={key}>
            <Text size="xs" c="dimmed" mb={4}>
              {key}:
            </Text>
            <ColoredJson value={formatted} />
          </Box>
        )
      })}
    </Stack>
  )
}

import type { DisplayPreferences } from "src/settings/displayPreferences"

type LogLineProps = {
  line: LogEntry
  expanded: boolean
  displayPreferences: DisplayPreferences
  onToggle: () => void
}

function LogLine({ line, expanded, displayPreferences, onToggle }: LogLineProps) {
  const level = line.level.toLowerCase()
  const displayMessage = formatLogDisplayMessage(line)
  const displayContext = logContextForDisplay(line.context)
  const expandable = hasExpandableContext(displayContext)

  return (
    <Box
      px="sm"
      py={4}
      className="log-line"
      style={{
        fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace",
        fontSize: 13,
        lineHeight: 1.45,
        borderBottom: "1px solid var(--mantine-color-dark-4)",
      }}
    >
      <Group gap="xs" wrap="nowrap" align={expanded ? "flex-start" : "center"}>
        <Text span c="dimmed" style={{ minWidth: 72, flexShrink: 0 }}>
          {formatTimestamp(line.ts, displayPreferences)}
        </Text>
        <LogLevelBadge level={level} fixedWidth />
        {line.logger ? <LogLoggerLabel logger={line.logger} /> : null}
        <Box style={{ flex: 1, minWidth: 0, overflow: "hidden" }}>
          {expanded ? (
            <>
              <Text style={{ whiteSpace: "pre-wrap", wordBreak: "break-word" }}>{displayMessage}</Text>
              <LogContextExpanded context={displayContext} />
            </>
          ) : (
            <Box
              style={{
                whiteSpace: "nowrap",
                overflow: "hidden",
                textOverflow: "ellipsis",
              }}
            >
              <Text span>{displayMessage}</Text>
              {expandable ? <LogContextInline context={displayContext} /> : null}
            </Box>
          )}
        </Box>
        {expandable ? (
          <ActionIcon
            size="lg"
            miw={44}
            h={44}
            variant="subtle"
            aria-label={expanded ? "Collapse log details" : "Expand log details"}
            aria-expanded={expanded}
            onClick={onToggle}
            style={{ flexShrink: 0 }}
          >
            {expanded ? "▼" : "▶"}
          </ActionIcon>
        ) : null}
      </Group>
    </Box>
  )
}

export function LogViewer({ runId, isLive }: LogViewerProps) {
  const { preferences } = useDisplayPreferences()
  const parentRef = useRef<HTMLDivElement>(null)
  const [stickToBottom, setStickToBottom] = useState(true)
  const [levelFilters, setLevelFilters] = useState<LogLevel[]>([])
  const [search, setSearch] = useState("")
  const [expandedLineIds, setExpandedLineIds] = useState<Set<number>>(() => new Set())

  const historyQuery = useQuery({
    queryKey: ["runs", runId, "logs", levelFilters, search],
    queryFn: () =>
      listRunLogs(runId, {
        limit: 2000,
        level: levelFilters.length === 1 ? levelFilters[0] : undefined,
        search: search || undefined,
      }),
    enabled: !isLive,
  })

  const stream = useLogStream(runId, { enabled: isLive })

  const rawLines = isLive ? stream.lines : (historyQuery.data?.items ?? [])

  const filteredLines = useMemo(() => {
    const needle = search.trim().toLowerCase()
    const levelSet = new Set(levelFilters)
    return rawLines.filter((line) => {
      if (levelSet.size > 0 && !levelSet.has(line.level.toLowerCase() as LogLevel)) return false
      if (!needle) return true
      const haystack = `${formatLogDisplayMessage(line)} ${line.message} ${line.logger} ${JSON.stringify(line.context)}`.toLowerCase()
      return haystack.includes(needle)
    })
  }, [rawLines, levelFilters, search])

  const rowVirtualizer = useVirtualizer({
    count: filteredLines.length,
    getScrollElement: () => parentRef.current,
    estimateSize: (index) => {
      const line = filteredLines[index]
      return estimateLogLineHeight(line, expandedLineIds.has(line.id))
    },
    measureElement: (element) => element.getBoundingClientRect().height,
    overscan: 12,
  })

  useEffect(() => {
    rowVirtualizer.measure()
  }, [expandedLineIds, rowVirtualizer])

  const toggleExpanded = useCallback((lineId: number) => {
    setExpandedLineIds((current) => {
      const next = new Set(current)
      if (next.has(lineId)) next.delete(lineId)
      else next.add(lineId)
      return next
    })
  }, [])

  const scrollToBottom = useCallback(() => {
    if (filteredLines.length === 0) return
    rowVirtualizer.scrollToIndex(filteredLines.length - 1, { align: "end" })
    setStickToBottom(true)
  }, [filteredLines.length, rowVirtualizer])

  useEffect(() => {
    if (!stickToBottom) return
    scrollToBottom()
  }, [filteredLines.length, stickToBottom, scrollToBottom])

  const handleScrollPositionChange = ({ y }: { x: number; y: number }) => {
    const element = parentRef.current
    if (!element) return
    const distanceFromBottom = element.scrollHeight - y - element.clientHeight
    setStickToBottom(distanceFromBottom < 48)
  }

  return (
    <Stack gap="sm">
      <Stack gap="sm">
        <Group justify="space-between" align="center" wrap="wrap" gap="xs">
          <Group gap="xs">
            {isLive ? <LiveStreamIndicator connected={stream.connected} ended={stream.ended} error={stream.error} /> : null}
            <Text size="sm" c="dimmed">
              {filteredLines.length} line{filteredLines.length === 1 ? "" : "s"}
            </Text>
          </Group>
        </Group>
        <Group align="flex-end" wrap="wrap" gap="sm">
          <LogLevelMultiSelect label="Level" value={levelFilters} onChange={setLevelFilters} clearable />
          <TextInput
            label="Search"
            placeholder="Filter log text"
            value={search}
            onChange={(event) => setSearch(event.currentTarget.value)}
            w={{ base: "100%", sm: 260 }}
            style={{ flex: "1 1 200px" }}
          />
          <TimezonePreferenceControls compact />
        </Group>
      </Stack>

      <Box pos="relative">
        {isLive ? <LiveStreamAccent connected={stream.connected} ended={stream.ended} error={stream.error} /> : null}
        <ScrollArea
          viewportRef={parentRef}
          h={420}
          type="auto"
          offsetScrollbars
          onScrollPositionChange={handleScrollPositionChange}
          style={{
            border: "1px solid var(--mantine-color-dark-4)",
            borderRadius: "var(--mantine-radius-lg)",
            background: "var(--mantine-color-dark-7)",
          }}
        >
          <Box h={rowVirtualizer.getTotalSize()} pos="relative">
            {rowVirtualizer.getVirtualItems().map((virtualRow) => {
              const line = filteredLines[virtualRow.index]
              return (
                <Box
                  key={line.id}
                  ref={rowVirtualizer.measureElement}
                  data-index={virtualRow.index}
                  pos="absolute"
                  top={0}
                  left={0}
                  w="100%"
                  style={{ transform: `translateY(${virtualRow.start}px)` }}
                >
                  <LogLine
                    line={line}
                    expanded={expandedLineIds.has(line.id)}
                    displayPreferences={preferences}
                    onToggle={() => toggleExpanded(line.id)}
                  />
                </Box>
              )
            })}
          </Box>
          {!isLive && historyQuery.isLoading ? (
            <Text p="md" c="dimmed">
              Loading logs…
            </Text>
          ) : null}
          {!isLive && !historyQuery.isLoading && filteredLines.length === 0 ? (
            <Text p="md" c="dimmed">
              No log lines for this run.
            </Text>
          ) : null}
        </ScrollArea>

        {!stickToBottom && filteredLines.length > 0 ? (
          <Button size="xs" variant="filled" pos="absolute" bottom={12} right={12} onClick={scrollToBottom}>
            Jump to latest
          </Button>
        ) : null}
      </Box>
    </Stack>
  )
}
