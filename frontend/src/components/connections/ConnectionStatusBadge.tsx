import { Badge, Group } from "@mantine/core"

import type { ConnectionSummary } from "src/api/connections"
import { connectionStatusLabel, formatConnectionStatus, SERVICE_LABELS, statusColor } from "src/components/connections/connectionStatus"
import { ServiceLogo } from "src/components/connections/ServiceLogo"

interface ConnectionStatusBadgeProps {
  connection: ConnectionSummary
}

export function ConnectionStatusBadge({ connection }: ConnectionStatusBadgeProps) {
  const statusText = formatConnectionStatus(connection.status)
  const showStatusText = connection.status !== "ok"

  return (
    <Badge
      color={statusColor(connection.status)}
      variant="light"
      aria-label={`${SERVICE_LABELS[connection.service]}: ${connectionStatusLabel(connection.status)}`}
    >
      <Group gap={6} wrap="nowrap">
        <ServiceLogo service={connection.service} size={14} />
        <span style={{ fontSize: "var(--mantine-font-size-xs)", fontWeight: 500 }}>{SERVICE_LABELS[connection.service]}</span>
        {showStatusText ? <span style={{ fontSize: "var(--mantine-font-size-xs)" }}>{statusText}</span> : null}
      </Group>
    </Badge>
  )
}
