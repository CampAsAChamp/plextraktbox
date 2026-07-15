import { Badge, Tooltip } from "@mantine/core";
import { formatVersionLabel, useHealthQuery } from "../../api/health";

export function ApiHealthBadge() {
  const { data, isError } = useHealthQuery();

  if (data) {
    const label = formatVersionLabel(data);
    const degraded = data.status === "degraded";
    const tooltipParts = [`plextraktbox ${label}`];
    if (degraded) {
      tooltipParts.push("degraded");
      if (!data.db_writable) tooltipParts.push("db not writable");
      if (!data.scheduler_running) tooltipParts.push("scheduler stopped");
    }
    if (data.built_at) {
      tooltipParts.push(`built ${data.built_at}`);
    }
    const tooltip = tooltipParts.join(" · ");

    return (
      <Tooltip label={tooltip} withArrow>
        <Badge color={degraded ? "yellow" : "green"} variant="light">
          {degraded ? "⚠" : "✓"} API · {label}
        </Badge>
      </Tooltip>
    );
  }

  if (isError) {
    return (
      <Badge color="red" variant="light">
        API unreachable
      </Badge>
    );
  }

  return (
    <Badge color="gray" variant="light">
      connecting…
    </Badge>
  );
}
