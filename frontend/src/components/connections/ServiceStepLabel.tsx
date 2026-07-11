import { Group, Text } from "@mantine/core";
import type { ConnectionSummary, Service } from "../../api/connections";
import { SERVICE_LABELS } from "./connectionStatus";
import { StatusCheckIcon } from "./StatusCheckIcon";

interface ServiceStepLabelProps {
  service: Service;
  connection: ConnectionSummary | undefined;
}

export function ServiceStepLabel({ service, connection }: ServiceStepLabelProps) {
  const connected = connection?.status === "ok";

  return (
    <Group gap={4} justify="center" wrap="nowrap">
      <Text component="span" size="sm" fw={500}>
        {SERVICE_LABELS[service]}
      </Text>
      {connected ? (
        <span style={{ color: "var(--mantine-color-green-6)", display: "inline-flex" }}>
          <StatusCheckIcon size={12} />
        </span>
      ) : null}
    </Group>
  );
}
