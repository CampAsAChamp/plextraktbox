import { Group, Text, Tooltip } from "@mantine/core";
import type { ReactNode } from "react";

function StrokeIcon({ size = 14, children }: { size?: number; children: ReactNode }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden
    >
      {children}
    </svg>
  );
}

/** Double check — matched across services. */
function MatchIcon({ size = 14 }: { size?: number }) {
  return (
    <StrokeIcon size={size}>
      <path d="M18 6 7 17l-5-5" />
      <path d="m22 10-10.5 10.5L8 16" />
    </StrokeIcon>
  );
}

function AddedIcon({ size = 14 }: { size?: number }) {
  return (
    <StrokeIcon size={size}>
      <circle cx="12" cy="12" r="10" />
      <path d="M12 8v8" />
      <path d="M8 12h8" />
    </StrokeIcon>
  );
}

function ErrorsIcon({ size = 14 }: { size?: number }) {
  return (
    <StrokeIcon size={size}>
      <circle cx="12" cy="12" r="10" />
      <path d="M12 8v4" />
      <path d="M12 16h.01" />
    </StrokeIcon>
  );
}

type RunSummaryStatsProps = {
  matched: number;
  added: number;
  errors: number;
};

function Stat({
  label,
  value,
  icon,
  color,
}: {
  label: string;
  value: number;
  icon: ReactNode;
  color?: string;
}) {
  return (
    <Tooltip label={`${label}: ${value}`} withArrow>
      <Group
        gap={4}
        wrap="nowrap"
        c={color}
        aria-label={`${label} ${value}`}
        style={{ cursor: "default" }}
      >
        {icon}
        <Text size="xs" span fw={600}>
          {value}
        </Text>
      </Group>
    </Tooltip>
  );
}

/** Compact matched / added / errors counts with icons (tooltips carry labels). */
export function RunSummaryStats({ matched, added, errors }: RunSummaryStatsProps) {
  return (
    <Group gap="sm" wrap="wrap">
      <Stat label="Matched" value={matched} icon={<MatchIcon size={15} />} />
      <Stat label="Added" value={added} icon={<AddedIcon size={15} />} />
      <Stat
        label="Errors"
        value={errors}
        icon={<ErrorsIcon size={15} />}
        color={errors > 0 ? "red.4" : undefined}
      />
    </Group>
  );
}
