import { Group } from "@mantine/core"
import type { ReactNode } from "react"

export function FieldLabel({ icon, children }: { icon: ReactNode; children: ReactNode }) {
  return (
    <Group gap={6} wrap="nowrap">
      <span style={{ display: "inline-flex", color: "var(--mantine-color-dimmed)" }}>{icon}</span>
      <span>{children}</span>
    </Group>
  )
}
