import { Accordion, Badge, Group, ScrollArea, Table, Text } from "@mantine/core";
import type { DataType } from "src/api/jobs";
import type { Service } from "src/api/connections";
import { SERVICE_LABELS } from "src/components/connections/connectionStatus";
import { ServiceLogo } from "src/components/connections/ServiceLogo";
import { DataTypeBadge } from "src/components/services/DataTypeBadge";
import { RoundedTable } from "src/components/table/RoundedTable";

export interface UnmatchedItem {
  source: string;
  data_type: string;
  title: string;
  source_key: string;
  reason: string;
}

const DATA_TYPES = new Set<DataType>(["watchlist", "ratings", "watched"]);

function isService(value: string): value is Service {
  return value in SERVICE_LABELS;
}

function isDataType(value: string): value is DataType {
  return DATA_TYPES.has(value as DataType);
}

function parseUnmatchedItems(raw: unknown): UnmatchedItem[] {
  if (!Array.isArray(raw)) return [];

  return raw.flatMap((entry) => {
    if (!entry || typeof entry !== "object") return [];
    const item = entry as Record<string, unknown>;
    if (typeof item.title !== "string" || typeof item.reason !== "string") return [];

    return [
      {
        source: typeof item.source === "string" ? item.source : "unknown",
        data_type: typeof item.data_type === "string" ? item.data_type : "unknown",
        title: item.title,
        source_key: typeof item.source_key === "string" ? item.source_key : item.title,
        reason: item.reason,
      },
    ];
  });
}

interface UnmatchedItemsSectionProps {
  items: unknown;
}

export function UnmatchedItemsSection({ items }: UnmatchedItemsSectionProps) {
  const parsedItems = parseUnmatchedItems(items);
  if (parsedItems.length === 0) return null;

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
          <ScrollArea.Autosize mah={420} type="auto">
            <RoundedTable striped highlightOnHover>
              <Table.Thead>
                <Table.Tr>
                  <Table.Th w={130} hiddenFrom="sm">
                    Service
                  </Table.Th>
                  <Table.Th>Title</Table.Th>
                  <Table.Th w={140} hiddenFrom="sm">
                    Type
                  </Table.Th>
                  <Table.Th>Reason</Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {parsedItems.map((item, index) => (
                  <Table.Tr key={`${item.source}-${item.source_key}-${item.reason}-${index}`}>
                    <Table.Td hiddenFrom="sm">
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
                      <Text size="sm">{item.title}</Text>
                    </Table.Td>
                    <Table.Td hiddenFrom="sm">
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
                  </Table.Tr>
                ))}
              </Table.Tbody>
            </RoundedTable>
          </ScrollArea.Autosize>
        </Accordion.Panel>
      </Accordion.Item>
    </Accordion>
  );
}
