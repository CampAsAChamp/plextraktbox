import { Box, Group, Select, TableOfContents, Text, useMantineTheme } from "@mantine/core"
import type { ComponentType, ReactNode } from "react"

import { ArrowLeftRightIcon } from "src/components/icons/ArrowLeftRightIcon"
import { BellIcon } from "src/components/icons/BellIcon"
import { CheckIcon } from "src/components/icons/CheckIcon"
import { ClockIcon } from "src/components/icons/ClockIcon"
import { FilterIcon } from "src/components/icons/FilterIcon"
import { IdCardIcon } from "src/components/icons/IdCardIcon"
import { ListIcon } from "src/components/icons/ListIcon"
import { ScaleIcon } from "src/components/icons/ScaleIcon"

export const JOB_FORM_SECTIONS = [
  { id: "job-name", value: "Name", depth: 1 },
  { id: "job-type", value: "Job Type", depth: 1 },
  { id: "job-data-types", value: "Data types", depth: 1 },
  { id: "job-source-of-truth", value: "Source of truth", depth: 1 },
  { id: "job-schedule", value: "Schedule", depth: 1 },
  { id: "job-options", value: "Options", depth: 1 },
  { id: "job-excludes", value: "Exclude ids", depth: 1 },
  { id: "job-notifications", value: "Notifications", depth: 1 },
] as const

export type JobFormSectionId = (typeof JOB_FORM_SECTIONS)[number]["id"]

export const JOB_FORM_SECTION_ICONS: Record<JobFormSectionId, ComponentType<{ size?: number }>> = {
  "job-name": IdCardIcon,
  "job-type": ArrowLeftRightIcon,
  "job-data-types": ListIcon,
  "job-source-of-truth": ScaleIcon,
  "job-schedule": ClockIcon,
  "job-options": CheckIcon,
  "job-excludes": FilterIcon,
  "job-notifications": BellIcon,
}

const SECTION_LABELS = Object.fromEntries(JOB_FORM_SECTIONS.map((section) => [section.id, section.value])) as Record<
  JobFormSectionId,
  string
>

/** Section heading with the same icon used in the job form TOC. */
export function JobFormSectionTitle({
  sectionId,
  children,
  iconSize = 14,
}: {
  sectionId: JobFormSectionId
  children?: ReactNode
  iconSize?: number
}) {
  const Icon = JOB_FORM_SECTION_ICONS[sectionId]
  return (
    <Group gap={6} wrap="nowrap" align="center" display="inline-flex">
      <Icon size={iconSize} />
      <span>{children ?? SECTION_LABELS[sectionId]}</span>
    </Group>
  )
}

function scrollToSection(id: string) {
  document.getElementById(id)?.scrollIntoView({ behavior: "smooth", block: "start" })
}

/** Compact section jump for narrow viewports (desktop TOC is sticky aside). */
export function JobFormMobileNav() {
  return (
    <Select
      hiddenFrom="sm"
      aria-label="Jump to job form section"
      placeholder="Jump to section"
      data={JOB_FORM_SECTIONS.map((section) => ({
        value: section.id,
        label: section.value,
      }))}
      onChange={(value) => {
        if (value) scrollToSection(value)
      }}
      clearable
      styles={{
        input: { cursor: "pointer" },
        section: { cursor: "pointer" },
      }}
    />
  )
}

export function JobFormToc() {
  const theme = useMantineTheme()
  return (
    <Box component="nav" aria-label="Job form sections" visibleFrom="sm" w={200} style={{ position: "sticky", top: 80, flexShrink: 0 }}>
      <Text size="xs" tt="uppercase" c="dimmed" fw={600} mb="xs">
        On this page
      </Text>
      <TableOfContents
        variant="light"
        color={theme.primaryColor}
        size="sm"
        radius="sm"
        scrollSpyOptions={{
          selector: "[data-job-section]",
          getDepth: () => 1,
          getValue: (element) => element.getAttribute("data-job-section") ?? "",
        }}
        getControlProps={({ data }) => {
          const Icon = JOB_FORM_SECTION_ICONS[data.id as JobFormSectionId]
          return {
            onClick: () => data.getNode().scrollIntoView({ behavior: "smooth", block: "start" }),
            children: (
              <Group gap={6} wrap="nowrap" justify="flex-start">
                {Icon ? <Icon size={14} /> : null}
                <span>{data.value}</span>
              </Group>
            ),
          }
        }}
        initialData={[...JOB_FORM_SECTIONS]}
      />
    </Box>
  )
}
