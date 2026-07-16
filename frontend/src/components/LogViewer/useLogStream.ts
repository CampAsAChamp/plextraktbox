import { fetchEventSource } from "@microsoft/fetch-event-source";
import { useEffect, useRef, useState } from "react";
import type { LogEntry, StreamPayload } from "src/api/logs";
import { runLogsStreamUrl } from "src/api/logs";
import { showToast } from "src/toast";

type UseLogStreamOptions = {
  enabled: boolean;
  onEnd?: (status: string) => void;
};

export function useLogStream(runId: number, { enabled, onEnd }: UseLogStreamOptions) {
  const [lines, setLines] = useState<LogEntry[]>([]);
  const [connected, setConnected] = useState(false);
  const [ended, setEnded] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const lastIdRef = useRef(0);
  const onEndRef = useRef(onEnd);
  const errorToastedRef = useRef(false);
  onEndRef.current = onEnd;

  useEffect(() => {
    if (!enabled) {
      setConnected(false);
      setError(null);
      errorToastedRef.current = false;
      return;
    }

    let cancelled = false;
    const controller = new AbortController();
    setError(null);
    errorToastedRef.current = false;

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
              setError(null);
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
          onerror(err) {
            if (controller.signal.aborted) return;
            setConnected(false);
            throw err;
          },
        });
      } catch {
        if (!controller.signal.aborted && !cancelled) {
          setConnected(false);
          const message = "Log stream disconnected";
          setError(message);
          if (!errorToastedRef.current) {
            errorToastedRef.current = true;
            showToast({ color: "red", message });
          }
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

  return { lines, connected, ended, error, lastId: lastIdRef.current };
}
