import { Accordion, ActionIcon, Badge, Group, Menu, ScrollArea, Table, Text, Tooltip } from "@mantine/core"
import { useMutation, useQueryClient } from "@tanstack/react-query"

import { ApiError } from "src/api/client"
import type { Service } from "src/api/connections"
import { appendJobExcludeIds } from "src/api/jobApi"
import type { DataType } from "src/api/jobs"
import { appendExcludeIds, type ExcludeIds } from "src/api/settings"
import { SERVICE_LABELS } from "src/components/connections/connectionStatus"
import { ServiceLogo } from "src/components/connections/ServiceLogo"
import { CopyAction } from "src/components/CopyAction"
import { DataTypeBadge } from "src/components/services/DataTypeBadge"
import { RoundedTable } from "src/components/table/RoundedTable"
import { showToast } from "src/toast"

export interface UnmatchedItem {
  source: string
  data_type: string
  title: string
  source_key: string
  reason: string
  identifiers: Partial<Record<"tmdb" | "imdb" | "tvdb", string>>
}

const DATA_TYPES = new Set<DataType>(["watchlist", "ratings", "watched"])
const ID_KEYS = ["tmdb", "imdb", "tvdb"] as const

function isService(value: string): value is Service {
  return value in SERVICE_LABELS
}

function isDataType(value: string): value is DataType {
  return DATA_TYPES.has(value as DataType)
}

function parseIdentifiers(raw: unknown): UnmatchedItem["identifiers"] {
  if (!raw || typeof raw !== "object") return {}
  const record = raw as Record<string, unknown>
  const out: UnmatchedItem["identifiers"] = {}
  for (const key of ID_KEYS) {
    const value = record[key]
    if (typeof value === "string" && value.trim()) {
      out[key] = value.trim()
    } else if (typeof value === "number" && Number.isFinite(value)) {
      out[key] = String(value)
    }
  }
  return out
}

function parseUnmatchedItems(raw: unknown): UnmatchedItem[] {
  if (!Array.isArray(raw)) return []

  return raw.flatMap((entry) => {
    if (!entry || typeof entry !== "object") return []
    const item = entry as Record<string, unknown>
    if (typeof item.title !== "string" || typeof item.reason !== "string") return []

    return [
      {
        source: typeof item.source === "string" ? item.source : "unknown",
        data_type: typeof item.data_type === "string" ? item.data_type : "unknown",
        title: item.title,
        source_key: typeof item.source_key === "string" ? item.source_key : item.title,
        reason: item.reason,
        identifiers: parseIdentifiers(item.identifiers),
      },
    ]
  })
}

function excludePayload(item: UnmatchedItem): ExcludeIds | null {
  const payload: ExcludeIds = { tmdb: [], imdb: [], tvdb: [] }
  let hasAny = false
  for (const key of ID_KEYS) {
    const value = item.identifiers[key]
    if (value) {
      payload[key] = [value]
      hasAny = true
    }
  }
  return hasAny ? payload : null
}

function idsLabel(item: UnmatchedItem): string {
  return ID_KEYS.filter((key) => item.identifiers[key])
    .map((key) => `${key}:${item.identifiers[key]}`)
    .join(", ")
}

interface UnmatchedItemsSectionProps {
  items: unknown
  jobId?: number
}

export function UnmatchedItemsSection({ items, jobId }: UnmatchedItemsSectionProps) {
  const queryClient = useQueryClient()
  const parsedItems = parseUnmatchedItems(items)

  const excludeMutation = useMutation({
    mutationFn: async ({ scope, payload }: { scope: "global" | "job"; payload: ExcludeIds }) => {
      if (scope === "global") {
        return appendExcludeIds(payload)
      }
      if (jobId === undefined) {
        throw new Error("Job id is required for per-job exclude")
      }
      return appendJobExcludeIds(jobId, payload)
    },
    onSuccess: (_data, variables) => {
      void queryClient.invalidateQueries({ queryKey: ["settings"] })
      void queryClient.invalidateQueries({ queryKey: ["jobs"] })
      showToast({
        color: "green",
        message: variables.scope === "global" ? "Added to global exclude list" : "Added to job exclude list",
      })
    },
    onError: (error: unknown) => {
      const message = error instanceof ApiError ? String(error.message) : "Could not update exclude list"
      showToast({ color: "red", message })
    },
  })

  if (parsedItems.length === 0) return null

  return (
    <Accordion variant="contained" chevronPosition="left">
      <Accordion.Item value="unmatched">
        <Accordion.Control>
          <Group gap="sm">
            <Text fw={500}>Unmatched items</Text>
            <Badge variant="light" color="orange">
              {parsedItems.length}
            </Badge>
          </Group>
        </Accordion.Control>
        <Accordion.Panel>
          <Text size="xs" c="dimmed" mb="sm">
            Excluding uses TMDB/IMDb/TVDB ids (episode rows exclude the whole show).
          </Text>
          <ScrollArea.Autosize mah={420} type="auto">
            <RoundedTable striped highlightOnHover>
              <Table.Thead>
                <Table.Tr>
                  <Table.Th w={130} visibleFrom="sm">
                    Service
                  </Table.Th>
                  <Table.Th>Title</Table.Th>
                  <Table.Th w={140} visibleFrom="sm">
                    Type
                  </Table.Th>
                  <Table.Th>Reason</Table.Th>
                  <Table.Th w={70}>Exclude</Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {parsedItems.map((item, index) => {
                  const payload = excludePayload(item)
                  const canExclude = payload !== null
                  return (
                    <Table.Tr key={`${item.source}-${item.source_key}-${item.reason}-${index}`}>
                      <Table.Td visibleFrom="sm">
                        <Group gap="xs" wrap="nowrap">
                          {isService(item.source) ? (
                            <>
                              <ServiceLogo service={item.source} size={18} />
                              <Text size="sm">{SERVICE_LABELS[item.source]}</Text>
                            </>
                          ) : (
                            <Text size="sm">{item.source}</Text>
                          )}
                        </Group>
                      </Table.Td>
                      <Table.Td>
                        <StackTitle item={item} />
                      </Table.Td>
                      <Table.Td visibleFrom="sm">
                        {isDataType(item.data_type) ? (
                          <DataTypeBadge dataType={item.data_type} size="xs" />
                        ) : (
                          <Text size="sm" c="dimmed">
                            {item.data_type}
                          </Text>
                        )}
                      </Table.Td>
                      <Table.Td>
                        <Text size="sm" c="dimmed">
                          {item.reason}
                        </Text>
                      </Table.Td>
                      <Table.Td>
                        <Menu withinPortal position="bottom-end">
                          <Menu.Target>
                            <Tooltip label={canExclude ? "Exclude this title" : "No TMDB/IMDb/TVDB ID available"} disabled={canExclude}>
                              <ActionIcon
                                variant="subtle"
                                aria-label={`Exclude ${item.title}`}
                                disabled={!canExclude || excludeMutation.isPending}
                              >
                                ⊘
                              </ActionIcon>
                            </Tooltip>
                          </Menu.Target>
                          <Menu.Dropdown>
                            <Menu.Label>{idsLabel(item) || "No ids"}</Menu.Label>
                            <Menu.Item
                              disabled={!canExclude}
                              onClick={() => {
                                if (payload) excludeMutation.mutate({ scope: "global", payload })
                              }}
                            >
                              Exclude globally
                            </Menu.Item>
                            <Menu.Item
                              disabled={!canExclude || jobId === undefined}
                              onClick={() => {
                                if (payload) excludeMutation.mutate({ scope: "job", payload })
                              }}
                            >
                              Exclude for this job
                            </Menu.Item>
                          </Menu.Dropdown>
                        </Menu>
                      </Table.Td>
                    </Table.Tr>
                  )
                })}
              </Table.Tbody>
            </RoundedTable>
          </ScrollArea.Autosize>
        </Accordion.Panel>
      </Accordion.Item>
    </Accordion>
  )
}

function StackTitle({ item }: { item: UnmatchedItem }) {
  const idLine = idsLabel(item)
  const copyValue = [item.title, idLine, item.source_key].filter(Boolean).join("\n")
  return (
    <Group gap="xs" wrap="nowrap" align="flex-start">
      <div style={{ flex: 1, minWidth: 0 }}>
        <Text size="sm">{item.title}</Text>
        {idLine ? (
          <Text size="xs" c="dimmed" ff="monospace">
            {idLine}
          </Text>
        ) : null}
      </div>
      <CopyAction value={copyValue} label="Copy title and ids" />
    </Group>
  )
}
