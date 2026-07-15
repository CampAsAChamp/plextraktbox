import { Badge, Box, Tooltip } from "@mantine/core";
import { formatVersionLabel, useHealthQuery } from "../../api/health";

/** Shown only when `/health` is degraded or unreachable — healthy stays out of the navbar. */
export function ApiHealthBadge() {
  const { data, isError } = useHealthQuery();

  if (data?.status === "ok") {
    return null;
  }

  if (data) {
    const label = formatVersionLabel(data);
    const tooltipParts = [`plextraktbox ${label}`, "degraded"];
    if (!data.db_writable) tooltipParts.push("db not writable");
    if (!data.scheduler_running) tooltipParts.push("scheduler stopped");
    if (data.built_at) {
      tooltipParts.push(`built ${data.built_at}`);
    }
    const tooltip = tooltipParts.join(" · ");

    return (
      <Tooltip label={tooltip} withArrow>
        <Badge color="yellow" variant="light">
          <Box component="span" hiddenFrom="sm">
            ⚠
          </Box>
          <Box component="span" visibleFrom="sm">
            ⚠ API · {label}
          </Box>
        </Badge>
      </Tooltip>
    );
  }

  if (isError) {
    return (
      <Badge color="red" variant="light">
        <Box component="span" hiddenFrom="sm">
          ✕
        </Box>
        <Box component="span" visibleFrom="sm">
          API unreachable
        </Box>
      </Badge>
    );
  }

  return null;
}
