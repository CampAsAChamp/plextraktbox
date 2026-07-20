import { Badge, type BadgeProps, Tooltip } from "@mantine/core"
import type { ReactNode } from "react"

import classes from "src/components/badges/ResponsiveBadge.module.css"

export type BadgeDisplayMode = "label" | "responsive"

type ResponsiveBadgeProps = {
  label: string
  color: BadgeProps["color"]
  icon: ReactNode
  mode?: BadgeDisplayMode
  size?: BadgeProps["size"]
  variant?: BadgeProps["variant"]
  className?: string
  /** Extra props for filter chips with a remove control, etc. */
  pr?: BadgeProps["pr"]
  rightSection?: BadgeProps["rightSection"]
}

/**
 * Text badge by default; below `md` with `mode="responsive"` shows a circular
 * icon-only badge + tooltip so list-table columns reclaim width.
 */
export function ResponsiveBadge({
  label,
  color,
  icon,
  mode = "label",
  size,
  variant = "light",
  className,
  pr,
  rightSection,
}: ResponsiveBadgeProps) {
  if (mode === "label") {
    return (
      <Badge color={color} variant={variant} size={size} className={className} pr={pr} rightSection={rightSection}>
        {label}
      </Badge>
    )
  }

  const iconClassName = className ? `${classes.iconBadge} ${className}` : classes.iconBadge

  return (
    <Tooltip label={label} withArrow>
      <span style={{ display: "inline-flex", alignItems: "center" }}>
        <Badge circle color={color} variant={variant} size="lg" className={iconClassName} hiddenFrom="md" aria-label={label}>
          {icon}
        </Badge>
        <Badge color={color} variant={variant} size={size} className={className} visibleFrom="md" pr={pr} rightSection={rightSection}>
          {label}
        </Badge>
      </span>
    </Tooltip>
  )
}
