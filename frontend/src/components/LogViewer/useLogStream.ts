import { fetchEventSource } from "@microsoft/fetch-event-source";
import { useEffect, useRef, useState } from "react";
import type { LogEntry, StreamPayload } from "../../api/logs";
import { runLogsStreamUrl } from "../../api/logs";

type UseLogStreamOptions = {
  enabled: boolean;
  onEnd?: (status: string) => void;
};

export function useLogStream(runId: number, { enabled, onEnd }: UseLogStreamOptions) {
  const [lines, setLines] = useState<LogEntry[]>([]);
  const [connected, setConnected] = useState(false);
  const [ended, setEnded] = useState(false);
  const lastIdRef = useRef(0);
  const onEndRef = useRef(onEnd);
  onEndRef.current = onEnd;

  useEffect(() => {
    if (!enabled) {
      setConnected(false);
      return;
    }

    let cancelled = false;
    const controller = new AbortController();

    const connect = async () => {
      if (cancelled) return;
      setConnected(true);

      try {
        await fetchEventSource(runLogsStreamUrl(runId, lastIdRef.current), {
          signal: controller.signal,
          credentials: "include",
          onmessage(message) {
            if (!message.data) return;
            const payload = JSON.parse(message.data) as StreamPayload;
            if (payload.type === "end") {
              setEnded(true);
              onEndRef.current?.(payload.status);
              controller.abort();
              return;
            }
            lastIdRef.current = Math.max(lastIdRef.current, payload.id);
            setLines((current) => {
              if (current.some((line) => line.id === payload.id)) {
                return current;
              }
              return [...current, payload];
            });
          },
          onclose() {
            setConnected(false);
          },
          onerror(error) {
            if (controller.signal.aborted) return;
            setConnected(false);
            throw error;
          },
        });
      } catch {
        if (!controller.signal.aborted && !cancelled) {
          setConnected(false);
        }
      }
    };

    void connect();

    return () => {
      cancelled = true;
      controller.abort();
      setConnected(false);
    };
  }, [enabled, runId]);

  return { lines, connected, ended, lastId: lastIdRef.current };
}
