import { Box, Group, Select, TableOfContents, Text } from "@mantine/core";
import type { ComponentType } from "react";
import { BellIcon } from "../../components/icons/BellIcon";
import { ClockIcon } from "../../components/icons/ClockIcon";
import { DatabaseIcon } from "../../components/icons/DatabaseIcon";
import { SyncIcon } from "../../components/icons/SyncIcon";
import { UserIcon } from "../../components/icons/UserIcon";

const INITIAL_SECTIONS = [
  { id: "settings-account", value: "Account", depth: 1 },
  { id: "settings-sync", value: "Sync defaults & safety", depth: 1 },
  { id: "settings-backup", value: "Backup", depth: 1 },
  { id: "settings-display", value: "Display preferences", depth: 1 },
  { id: "settings-notifications", value: "Notifications", depth: 1 },
] as const;

const SECTION_ICONS: Record<string, ComponentType<{ size?: number }>> = {
  "settings-account": UserIcon,
  "settings-sync": SyncIcon,
  "settings-backup": DatabaseIcon,
  "settings-display": ClockIcon,
  "settings-notifications": BellIcon,
};

function scrollToSection(id: string) {
  document.getElementById(id)?.scrollIntoView({ behavior: "smooth", block: "start" });
}

/** Compact section jump for narrow viewports (desktop TOC is sticky aside). */
export function SettingsMobileNav() {
  return (
    <Select
      hiddenFrom="sm"
      aria-label="Jump to settings section"
      placeholder="Jump to section"
      data={INITIAL_SECTIONS.map((section) => ({
        value: section.id,
        label: section.value,
      }))}
      onChange={(value) => {
        if (value) scrollToSection(value);
      }}
      clearable
      styles={{
        input: { cursor: "pointer" },
        section: { cursor: "pointer" },
      }}
    />
  );
}

export function SettingsToc() {
  return (
    <Box
      component="nav"
      aria-label="Settings sections"
      visibleFrom="sm"
      w={200}
      style={{ position: "sticky", top: 80, flexShrink: 0 }}
    >
      <Text size="xs" tt="uppercase" c="dimmed" fw={600} mb="xs">
        On this page
      </Text>
      <TableOfContents
        variant="light"
        color="amber"
        size="sm"
        radius="sm"
        scrollSpyOptions={{
          selector: "[data-settings-section]",
          getDepth: () => 1,
          getValue: (element) => element.getAttribute("data-settings-section") ?? "",
        }}
        getControlProps={({ data }) => {
          const Icon = SECTION_ICONS[data.id];
          return {
            onClick: () =>
              data.getNode().scrollIntoView({ behavior: "smooth", block: "start" }),
            children: (
              <Group gap={6} wrap="nowrap" justify="flex-start">
                {Icon ? <Icon size={14} /> : null}
                <span>{data.value}</span>
              </Group>
            ),
          };
        }}
        initialData={[...INITIAL_SECTIONS]}
      />
    </Box>
  );
}
