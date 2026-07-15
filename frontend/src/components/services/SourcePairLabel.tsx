import { Group, Text, Tooltip } from "@mantine/core";
import type { SourcePair } from "../../api/jobs";
import { ServiceLogo } from "../connections/ServiceLogo";
import { SERVICE_LABELS } from "../connections/connectionStatus";
import { SERVICE_TEXT_COLORS } from "./serviceBrand";

type SyncService = "plex" | "trakt" | "letterboxd";

const SOURCE_PAIR_SERVICES: Record<
  SourcePair,
  { from: SyncService; to: SyncService; bidirectional: boolean }
> = {
  plex_trakt: { from: "plex", to: "trakt", bidirectional: true },
  letterboxd_plex: { from: "letterboxd", to: "plex", bidirectional: false },
  letterboxd_trakt: { from: "letterboxd", to: "trakt", bidirectional: false },
};

function sourcePairLabelText(sourcePair: SourcePair): string {
  const { from, to, bidirectional } = SOURCE_PAIR_SERVICES[sourcePair];
  const arrow = bidirectional ? "↔" : "→";
  return `${SERVICE_LABELS[from]} ${arrow} ${SERVICE_LABELS[to]}`;
}

function ServiceName({ service }: { service: SyncService }) {
  return (
    <Text component="span" fw={600} style={{ color: SERVICE_TEXT_COLORS[service] }}>
      {SERVICE_LABELS[service]}
    </Text>
  );
}

function SourcePairIcons({
  from,
  to,
  bidirectional,
  logoSize,
}: {
  from: SyncService;
  to: SyncService;
  bidirectional: boolean;
  logoSize: number;
}) {
  const arrow = bidirectional ? "↔" : "→";
  const arrowSize = Math.round(logoSize * 0.85);

  return (
    <Group component="span" gap={4} wrap="nowrap" align="center" display="inline-flex">
      <ServiceLogo service={from} size={logoSize} />
      <Text
        component="span"
        fw={700}
        c="gray.7"
        aria-hidden
        style={{ fontSize: arrowSize, lineHeight: `${logoSize}px` }}
      >
        {arrow}
      </Text>
      <ServiceLogo service={to} size={logoSize} />
    </Group>
  );
}

export function SourcePairLabel({
  sourcePair,
  variant = "text",
  logoSize = 20,
}: {
  sourcePair: SourcePair;
  variant?: "text" | "logo" | "icons";
  logoSize?: number;
}) {
  const { from, to, bidirectional } = SOURCE_PAIR_SERVICES[sourcePair];
  const arrow = bidirectional ? "↔" : "→";
  const label = sourcePairLabelText(sourcePair);

  if (variant === "icons") {
    return (
      <Tooltip label={label} withArrow>
        <Group
          gap={4}
          wrap="nowrap"
          align="center"
          w="fit-content"
          aria-label={label}
          style={{ cursor: "default" }}
        >
          <SourcePairIcons
            from={from}
            to={to}
            bidirectional={bidirectional}
            logoSize={logoSize}
          />
        </Group>
      </Tooltip>
    );
  }

  if (variant === "logo") {
    return (
      <Group gap={6} wrap="nowrap" align="center" w="fit-content">
        <SourcePairIcons
          from={from}
          to={to}
          bidirectional={bidirectional}
          logoSize={logoSize}
        />
        <Text component="span" size="sm" style={{ lineHeight: `${logoSize}px` }}>
          <Text component="span" c="dimmed" inherit>
            (
          </Text>
          <ServiceName service={from} />
          <Text component="span" c="dimmed" inherit>
            {" "}
            {arrow}{" "}
          </Text>
          <ServiceName service={to} />
          <Text component="span" c="dimmed" inherit>
            )
          </Text>
        </Text>
      </Group>
    );
  }

  return (
    <Text component="span" size="sm">
      <ServiceName service={from} />
      <Text component="span" c="dimmed" inherit>
        {" "}
        {arrow}{" "}
      </Text>
      <ServiceName service={to} />
    </Text>
  );
}
