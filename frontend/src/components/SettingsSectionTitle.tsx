import { Group, Title } from "@mantine/core"
import type { ReactNode } from "react"

interface SettingsSectionTitleProps {
  icon: ReactNode
  children: ReactNode
}

export function SettingsSectionTitle({ icon, children }: SettingsSectionTitleProps) {
  return (
    <Group gap="xs" wrap="nowrap" align="center">
      {icon}
      <Title order={4}>{children}</Title>
    </Group>
  )
}
