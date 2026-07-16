import { Accordion, Group, Stack, Table, Text } from "@mantine/core"
import { Fragment } from "react"

import type { DataType } from "src/api/jobs"
import { SERVICE_LABELS } from "src/components/connections/connectionStatus"
import { ServiceLogo } from "src/components/connections/ServiceLogo"
import { JobFormSectionTitle } from "src/components/JobForm/JobFormToc"
import { DataTypeBadge } from "src/components/services/DataTypeBadge"
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
    <Accordion
      id="job-source-of-truth"
      data-job-section="Source of truth"
      variant="contained"
      chevronPosition="left"
      style={{ scrollMarginTop: 80 }}
    >
      <Accordion.Item value="source-of-truth">
        <Accordion.Control>
          <Text fw={500}>
            <JobFormSectionTitle sectionId="job-source-of-truth" />
          </Text>
        </Accordion.Control>
        <Accordion.Panel>
          <Stack gap="xs">
            <Text size="sm" c="dimmed">
              Each data type has one service that wins conflicts:
            </Text>
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
                        <DataTypeBadge dataType={row.dataType} />
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
        </Accordion.Panel>
      </Accordion.Item>
    </Accordion>
  )
}
