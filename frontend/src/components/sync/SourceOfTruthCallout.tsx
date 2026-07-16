import { Alert, Stack, Table, Text } from "@mantine/core"

import type { DataType } from "src/api/jobs"
import { DATA_TYPE_LABELS } from "src/api/jobs"
import { RoundedTable } from "src/components/table/RoundedTable"
import { SOURCE_OF_TRUTH } from "src/sync/sourceOfTruth"

interface SourceOfTruthCalloutProps {
  /** Data types enabled for the selected job pair — highlighted rows. */
  relevantTypes: DataType[]
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
                    <Text size="sm">{row.truth}</Text>
                  </Table.Td>
                  <Table.Td>
                    <Text size="sm">{row.writes}</Text>
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
