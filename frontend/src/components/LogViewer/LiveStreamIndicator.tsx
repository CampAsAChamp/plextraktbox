import { Badge, Box, Group } from "@mantine/core";
import { useMediaQuery } from "@mantine/hooks";
import classes from "./LiveStreamIndicator.module.css";

type LiveStreamIndicatorProps = {
  connected: boolean;
  ended: boolean;
};

type LiveStreamState = "streaming" | "connecting" | "complete";

function getLiveStreamState(connected: boolean, ended: boolean): LiveStreamState {
  if (ended) return "complete";
  if (connected) return "streaming";
  return "connecting";
}

const STATE_CONFIG: Record<
  LiveStreamState,
  { color: string; dotClass: string; label: string; ariaLabel: string; animate: boolean }
> = {
  streaming: {
    color: "green",
    dotClass: classes.dotGreen,
    label: "Live",
    ariaLabel: "Streaming logs live",
    animate: true,
  },
  connecting: {
    color: "yellow",
    dotClass: classes.dotYellow,
    label: "Connecting",
    ariaLabel: "Connecting to log stream",
    animate: true,
  },
  complete: {
    color: "gray",
    dotClass: classes.dotGray,
    label: "Complete",
    ariaLabel: "Log stream complete",
    animate: false,
  },
};

function LiveStreamDot({
  dotClass,
  animate,
  reduceMotion,
}: {
  dotClass: string;
  animate: boolean;
  reduceMotion: boolean;
}) {
  const shouldAnimate = animate && !reduceMotion;

  return (
    <Box className={`${classes.dot} ${dotClass}`}>
      {shouldAnimate ? <Box className={`${classes.dotRing} ${classes.animateRing}`} /> : null}
      <Box className={`${classes.dotCore} ${shouldAnimate ? classes.animateCore : ""}`} />
    </Box>
  );
}

export function LiveStreamIndicator({ connected, ended }: LiveStreamIndicatorProps) {
  const reduceMotion = useMediaQuery("(prefers-reduced-motion: reduce)") ?? false;
  const state = getLiveStreamState(connected, ended);
  const config = STATE_CONFIG[state];

  return (
    <Badge color={config.color} variant="light" aria-label={config.ariaLabel}>
      <Group gap={6} wrap="nowrap">
        <LiveStreamDot dotClass={config.dotClass} animate={config.animate} reduceMotion={reduceMotion} />
        <span>{config.label}</span>
      </Group>
    </Badge>
  );
}

type LiveStreamAccentProps = {
  connected: boolean;
  ended: boolean;
};

export function LiveStreamAccent({ connected, ended }: LiveStreamAccentProps) {
  const reduceMotion = useMediaQuery("(prefers-reduced-motion: reduce)") ?? false;
  const state = getLiveStreamState(connected, ended);

  if (state !== "streaming") return null;

  return (
    <div
      data-testid="live-stream-accent"
      className={`${classes.accent} ${reduceMotion ? "" : classes.animateAccent}`}
    />
  );
}
