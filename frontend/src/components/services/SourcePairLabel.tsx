import { Text } from "@mantine/core";
import type { SourcePair } from "../../api/jobs";
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

function ServiceName({ service }: { service: SyncService }) {
  return (
    <Text component="span" fw={600} style={{ color: SERVICE_TEXT_COLORS[service] }}>
      {SERVICE_LABELS[service]}
    </Text>
  );
}

export function SourcePairLabel({ sourcePair }: { sourcePair: SourcePair }) {
  const { from, to, bidirectional } = SOURCE_PAIR_SERVICES[sourcePair];

  return (
    <Text component="span" size="sm">
      <ServiceName service={from} />
      <Text component="span" c="dimmed" inherit>
        {" "}
        {bidirectional ? "↔" : "→"}{" "}
      </Text>
      <ServiceName service={to} />
    </Text>
  );
}
