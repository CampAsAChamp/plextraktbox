import { Badge } from "@mantine/core";
import type { DataType } from "../../api/jobs";
import { DATA_TYPE_COLORS, DATA_TYPE_LABELS } from "../../api/jobs";

interface DataTypeBadgeProps {
  dataType: DataType;
  size?: "xs" | "sm" | "md" | "lg" | "xl";
}

export function DataTypeBadge({ dataType, size = "sm" }: DataTypeBadgeProps) {
  return (
    <Badge color={DATA_TYPE_COLORS[dataType]} size={size} variant="light">
      {DATA_TYPE_LABELS[dataType]}
    </Badge>
  );
}
