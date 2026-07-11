import {
  ActionIcon,
  Badge,
  Box,
  Button,
  Group,
  ScrollArea,
  Select,
  Stack,
  Text,
  TextInput,
  Tooltip,
} from "@mantine/core";
import { useVirtualizer } from "@tanstack/react-virtual";
import { useQuery } from "@tanstack/react-query";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { listRunLogs, type LogEntry } from "../../api/logs";
import {
  estimateLogLineHeight,
  formatContextValue,
  formatContextValueCompact,
  hasExpandableContext,
  LOG_LOGGER_BRACKET_COLOR,
  LOG_LOGGER_NAME_COLOR,
  shouldPrettyPrintContextValue,
  shouldRenderStatusBadge,
  shouldSyntaxHighlightContextValue,
} from "./logFormat";
import { ColoredJson, ColoredJsonSpans, JSON_SYNTAX_COLORS } from "./ColoredJson";
import { RunStatusBadge } from "../runs/RunBadges";
import { useDisplayPreferences } from "../../settings/DisplayPreferencesProvider";
import { TimezonePreferenceControls } from "../../settings/TimezonePreferenceControls";
import { formatTimestamp } from "../../utils/dateTimeFormat";
import { LiveStreamAccent, LiveStreamIndicator } from "./LiveStreamIndicator";
import { useLogStream } from "./useLogStream";

const LEVEL_OPTIONS = [
  { value: "", label: "All levels" },
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

type LogViewerProps = {
  runId: number;
  isLive: boolean;
};

function LogLoggerLabel({ logger }: { logger: string }) {
  return (
    <Box component="span" style={{ minWidth: 120, flexShrink: 0 }}>
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
  );
}

function InlineContextValue({ value }: { value: unknown }) {
  const compact = formatContextValueCompact(value);
  if (shouldSyntaxHighlightContextValue(value)) {
    return <ColoredJsonSpans value={compact} />;
  }

  return (
    <Box component="span" style={{ color: JSON_SYNTAX_COLORS.string }}>
      {compact}
    </Box>
  );
}

function LogContextInline({ context }: { context: Record<string, unknown> }) {
  const entries = Object.entries(context);
  if (entries.length === 0) return null;

  return (
    <>
      {entries.map(([key, value]) => {
        if (shouldRenderStatusBadge(key, value)) {
          return (
            <Box
              key={key}
              component="span"
              ml={8}
              style={{ display: "inline-flex", alignItems: "center", gap: 4, verticalAlign: "middle" }}
            >
              <Text span size="xs" c="dimmed">
                {key}
              </Text>
              <RunStatusBadge status={value} />
            </Box>
          );
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
        );
      })}
    </>
  );
}

function LogContextExpanded({ context }: { context: Record<string, unknown> }) {
  const entries = Object.entries(context);
  if (entries.length === 0) return null;

  return (
    <Stack gap={6} mt={6} pl={4}>
      {entries.map(([key, value]) => {
        const formatted = formatContextValue(value);
        if (shouldRenderStatusBadge(key, value)) {
          return (
            <Group key={key} gap={6} wrap="nowrap" align="center">
              <Text size="xs" c="dimmed">
                {key}
              </Text>
              <RunStatusBadge status={value} />
            </Group>
          );
        }

        if (!shouldPrettyPrintContextValue(value)) {
          return (
            <Text key={key} size="xs" c="dimmed">
              {key}={formatted}
            </Text>
          );
        }

        return (
          <Box key={key}>
            <Text size="xs" c="dimmed" mb={4}>
              {key}:
            </Text>
            <ColoredJson value={formatted} />
          </Box>
        );
      })}
    </Stack>
  );
}

import type { DisplayPreferences } from "../../settings/displayPreferences";

type LogLineProps = {
  line: LogEntry;
  expanded: boolean;
  displayPreferences: DisplayPreferences;
  onToggle: () => void;
};

function LogLine({ line, expanded, displayPreferences, onToggle }: LogLineProps) {
  const level = line.level.toLowerCase();
  const expandable = hasExpandableContext(line.context);

  return (
    <Box
      px="sm"
      py={4}
      style={{
        fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace",
        fontSize: 13,
        lineHeight: 1.45,
        borderBottom: "1px solid var(--mantine-color-dark-4)",
      }}
    >
      <Group gap="xs" wrap="nowrap" align={expanded ? "flex-start" : "center"}>
        <Text span c="dimmed" style={{ minWidth: 92, flexShrink: 0 }}>
          {formatTimestamp(line.ts, displayPreferences)}
        </Text>
        <Badge
          size="xs"
          variant="light"
          color={LEVEL_COLORS[level] ?? "gray"}
          style={{ minWidth: 52, textTransform: "uppercase", flexShrink: 0 }}
        >
          {level}
        </Badge>
        {line.logger ? <LogLoggerLabel logger={line.logger} /> : null}
        <Box style={{ flex: 1, minWidth: 0, overflow: "hidden" }}>
          {expanded ? (
            <>
              <Text style={{ whiteSpace: "pre-wrap", wordBreak: "break-word" }}>{line.message}</Text>
              <LogContextExpanded context={line.context} />
            </>
          ) : (
            <Box
              style={{
                whiteSpace: "nowrap",
                overflow: "hidden",
                textOverflow: "ellipsis",
              }}
            >
              <Text span>{line.message}</Text>
              {expandable ? <LogContextInline context={line.context} /> : null}
            </Box>
          )}
        </Box>
        {expandable ? (
          <Tooltip label={expanded ? "Collapse details" : "Expand details"}>
            <ActionIcon
              size="sm"
              variant="subtle"
              aria-label={expanded ? "Collapse log details" : "Expand log details"}
              aria-expanded={expanded}
              onClick={onToggle}
              style={{ flexShrink: 0 }}
            >
              {expanded ? "▼" : "▶"}
            </ActionIcon>
          </Tooltip>
        ) : null}
      </Group>
    </Box>
  );
}

export function LogViewer({ runId, isLive }: LogViewerProps) {
  const { preferences } = useDisplayPreferences();
  const parentRef = useRef<HTMLDivElement>(null);
  const [stickToBottom, setStickToBottom] = useState(true);
  const [levelFilter, setLevelFilter] = useState("");
  const [search, setSearch] = useState("");
  const [expandedLineIds, setExpandedLineIds] = useState<Set<number>>(() => new Set());

  const historyQuery = useQuery({
    queryKey: ["runs", runId, "logs", levelFilter, search],
    queryFn: () =>
      listRunLogs(runId, {
        limit: 2000,
        level: levelFilter || undefined,
        search: search || undefined,
      }),
    enabled: !isLive,
  });

  const stream = useLogStream(runId, { enabled: isLive });

  const rawLines = isLive ? stream.lines : (historyQuery.data?.items ?? []);

  const filteredLines = useMemo(() => {
    const needle = search.trim().toLowerCase();
    return rawLines.filter((line) => {
      if (levelFilter && line.level.toLowerCase() !== levelFilter) return false;
      if (!needle) return true;
      const haystack = `${line.message} ${line.logger} ${JSON.stringify(line.context)}`.toLowerCase();
      return haystack.includes(needle);
    });
  }, [rawLines, levelFilter, search]);

  const rowVirtualizer = useVirtualizer({
    count: filteredLines.length,
    getScrollElement: () => parentRef.current,
    estimateSize: (index) => {
      const line = filteredLines[index];
      return estimateLogLineHeight(line, expandedLineIds.has(line.id));
    },
    measureElement: (element) => element.getBoundingClientRect().height,
    overscan: 12,
  });

  useEffect(() => {
    rowVirtualizer.measure();
  }, [expandedLineIds, rowVirtualizer]);

  const toggleExpanded = useCallback((lineId: number) => {
    setExpandedLineIds((current) => {
      const next = new Set(current);
      if (next.has(lineId)) next.delete(lineId);
      else next.add(lineId);
      return next;
    });
  }, []);

  const scrollToBottom = useCallback(() => {
    if (filteredLines.length === 0) return;
    rowVirtualizer.scrollToIndex(filteredLines.length - 1, { align: "end" });
    setStickToBottom(true);
  }, [filteredLines.length, rowVirtualizer]);

  useEffect(() => {
    if (!stickToBottom) return;
    scrollToBottom();
  }, [filteredLines.length, stickToBottom, scrollToBottom]);

  const handleScrollPositionChange = ({ y }: { x: number; y: number }) => {
    const element = parentRef.current;
    if (!element) return;
    const distanceFromBottom = element.scrollHeight - y - element.clientHeight;
    setStickToBottom(distanceFromBottom < 48);
  };

  return (
    <Stack gap="sm">
      <Group justify="space-between" align="flex-end">
        <Group align="flex-end">
          <Select
            label="Level"
            data={LEVEL_OPTIONS}
            value={levelFilter}
            onChange={(value) => setLevelFilter(value ?? "")}
            w={160}
            allowDeselect={false}
          />
          <TextInput
            label="Search"
            placeholder="Filter log text"
            value={search}
            onChange={(event) => setSearch(event.currentTarget.value)}
            w={260}
          />
          <TimezonePreferenceControls compact />
        </Group>
        <Group gap="xs">
          {isLive ? (
            <LiveStreamIndicator connected={stream.connected} ended={stream.ended} />
          ) : null}
          <Text size="sm" c="dimmed">
            {filteredLines.length} line{filteredLines.length === 1 ? "" : "s"}
          </Text>
        </Group>
      </Group>

      <Box pos="relative">
        {isLive ? (
          <LiveStreamAccent connected={stream.connected} ended={stream.ended} />
        ) : null}
        <ScrollArea
          viewportRef={parentRef}
          h={420}
          type="auto"
          offsetScrollbars
          onScrollPositionChange={handleScrollPositionChange}
          style={{
            border: "1px solid var(--mantine-color-dark-4)",
            borderRadius: 8,
            background: "var(--mantine-color-dark-7)",
          }}
        >
          <Box h={rowVirtualizer.getTotalSize()} pos="relative">
            {rowVirtualizer.getVirtualItems().map((virtualRow) => {
              const line = filteredLines[virtualRow.index];
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
              );
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
          <Button
            size="xs"
            variant="filled"
            pos="absolute"
            bottom={12}
            right={12}
            onClick={scrollToBottom}
          >
            Jump to latest
          </Button>
        ) : null}
      </Box>
    </Stack>
  );
}
