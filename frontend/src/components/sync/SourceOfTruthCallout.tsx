import { Alert, Group, Stack, Table, Text } from "@mantine/core"
import { Fragment } from "react"

import type { DataType } from "src/api/jobs"
import { DATA_TYPE_LABELS } from "src/api/jobs"
import { SERVICE_LABELS } from "src/components/connections/connectionStatus"
import { ServiceLogo } from "src/components/connections/ServiceLogo"
import { RoundedTable } from "src/components/table/RoundedTable"
import type { SourceOfTruthWrite, SyncService } from "src/sync/sourceOfTruth"
import { SOURCE_OF_TRUTH } from "src/sync/sourceOfTruth"

interface SourceOfTruthCalloutProps {
  /** Data types enabled for the selected job pair — highlighted rows. */
  relevantTypes: DataType[]
}

function ServiceWithLogo({ service, action }: { service: SyncService; action?: string }) {
  return (
    <Group gap={6} wrap="nowrap" align="center" display="inline-flex">
      <ServiceLogo service={service} size={16} />
      <Text size="sm" component="span">
        {SERVICE_LABELS[service]}
        {action ? (
          <Text size="sm" c="dimmed" component="span">
            {" "}
            {action}
          </Text>
        ) : null}
      </Text>
    </Group>
  )
}

function WritesCell({ writes }: { writes: SourceOfTruthWrite[] }) {
  return (
    <Group gap={6} wrap="wrap" align="center">
      {writes.map((write, index) => (
        <Fragment key={`${write.service}-${write.action ?? ""}`}>
          {index > 0 ? (
            <Text size="sm" c="dimmed" component="span">
              +
            </Text>
          ) : null}
          <ServiceWithLogo service={write.service} action={write.action} />
        </Fragment>
      ))}
    </Group>
  )
}

export function SourceOfTruthCallout({ relevantTypes }: SourceOfTruthCalloutProps) {
  const relevant = new Set(relevantTypes)

  return (
    <Alert variant="light" title="Source of truth" color="blue">
      <Stack gap="xs">
        <Text size="sm">Each data type has one service that wins conflicts:</Text>
        <RoundedTable>
          <Table.Thead>
            <Table.Tr>
              <Table.Th>Type</Table.Th>
              <Table.Th>Truth</Table.Th>
              <Table.Th>Writes</Table.Th>
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {SOURCE_OF_TRUTH.map((row) => {
              const active = relevant.has(row.dataType)
              return (
                <Table.Tr key={row.dataType} opacity={active ? 1 : 0.45}>
                  <Table.Td>
                    <Text size="sm" fw={active ? 600 : 400}>
                      {DATA_TYPE_LABELS[row.dataType]}
                    </Text>
                  </Table.Td>
                  <Table.Td>
                    <ServiceWithLogo service={row.truth} />
                  </Table.Td>
                  <Table.Td>
                    <WritesCell writes={row.writes} />
                    {row.note ? (
                      <Text size="xs" c="dimmed">
                        {row.note}
                      </Text>
                    ) : null}
                  </Table.Td>
                </Table.Tr>
              )
            })}
          </Table.Tbody>
        </RoundedTable>
      </Stack>
    </Alert>
  )
}
