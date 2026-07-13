import { Badge, Tooltip } from "@mantine/core";
import { formatVersionLabel, useHealthQuery } from "../../api/health";

export function ApiHealthBadge() {
  const { data, isError } = useHealthQuery();

  if (data) {
    const label = formatVersionLabel(data);
    const tooltipParts = [`plextraktbox ${label}`];
    if (data.built_at) {
      tooltipParts.push(`built ${data.built_at}`);
    }
    const tooltip = tooltipParts.join(" · ");

    return (
      <Tooltip label={tooltip} withArrow>
        <Badge color="green" variant="light">
          ✓ API · {label}
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
