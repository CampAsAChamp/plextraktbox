import type { ReactNode } from "react"

import type { DataType } from "src/api/jobs"
import { DATA_TYPE_COLORS, DATA_TYPE_LABELS } from "src/api/jobs"
import { type BadgeDisplayMode, ResponsiveBadge } from "src/components/badges/ResponsiveBadge"
import { CheckIcon } from "src/components/icons/CheckIcon"
import { ListIcon } from "src/components/icons/ListIcon"
import { ScaleIcon } from "src/components/icons/ScaleIcon"

interface DataTypeBadgeProps {
  dataType: DataType
  size?: "xs" | "sm" | "md" | "lg" | "xl"
  mode?: BadgeDisplayMode
}

function dataTypeIcon(dataType: DataType): ReactNode {
  if (dataType === "watchlist") return <ListIcon size={14} />
  if (dataType === "ratings") return <ScaleIcon size={14} />
  return <CheckIcon size={14} />
}

export function DataTypeBadge({ dataType, size = "sm", mode = "label" }: DataTypeBadgeProps) {
  return (
    <ResponsiveBadge
      label={DATA_TYPE_LABELS[dataType]}
      color={DATA_TYPE_COLORS[dataType]}
      icon={dataTypeIcon(dataType)}
      size={size}
      mode={mode}
    />
  )
}
