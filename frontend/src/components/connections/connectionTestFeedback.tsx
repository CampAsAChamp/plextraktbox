import { Button } from "@mantine/core";
import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError } from "src/api/client";
import type { ConnectionTestResult } from "src/api/connections";
import { showToast } from "src/toast";
import { StatusCheckIcon } from "src/components/connections/StatusCheckIcon";
import { StatusXIcon } from "src/components/connections/StatusXIcon";
import { TestConnectionIcon } from "src/components/connections/TestConnectionIcon";
import classes from "./connectionTestFeedback.module.css";

export type ConnectionTestStatus = "idle" | "success" | "error";

const SUCCESS_BUTTON_RESET_MS = 1500;

export function showConnectionTestResult(result: ConnectionTestResult) {
  showToast({
    color: result.ok ? "green" : "red",
    message: result.message,
  });
}

export function showConnectionTestError(error: unknown, fallbackMessage: string) {
  showToast({
    color: "red",
    message: error instanceof ApiError ? String(error.message) : fallbackMessage,
  });
}

export function useConnectionTestFeedback() {
  const [testStatus, setTestStatus] = useState<ConnectionTestStatus>("idle");
  const resetTimerRef = useRef<number | null>(null);

  const clearResetTimer = useCallback(() => {
    if (resetTimerRef.current !== null) {
      window.clearTimeout(resetTimerRef.current);
      resetTimerRef.current = null;
    }
  }, []);

  const resetTestStatus = useCallback(() => {
    clearResetTimer();
    setTestStatus("idle");
  }, [clearResetTimer]);

  const onTestSuccess = useCallback(
    (result: ConnectionTestResult) => {
      clearResetTimer();
      showConnectionTestResult(result);
      if (result.ok) {
        setTestStatus("success");
        resetTimerRef.current = window.setTimeout(() => {
          resetTimerRef.current = null;
          setTestStatus("idle");
        }, SUCCESS_BUTTON_RESET_MS);
        return;
      }
      setTestStatus("error");
    },
    [clearResetTimer],
  );

  const onTestError = useCallback(
    (error: unknown, fallbackMessage: string) => {
      clearResetTimer();
      setTestStatus("error");
      showConnectionTestError(error, fallbackMessage);
    },
    [clearResetTimer],
  );

  useEffect(() => () => clearResetTimer(), [clearResetTimer]);

  return { testStatus, onTestSuccess, onTestError, resetTestStatus };
}

export function TestConnectionButton({
  testStatus,
  loading,
  disabled,
  onClick,
}: {
  testStatus: ConnectionTestStatus;
  loading?: boolean;
  disabled?: boolean;
  onClick: () => void;
}) {
  return (
    <Button
      type="button"
      variant="light"
      classNames={{ root: classes.button, section: classes.section }}
      data-status={testStatus}
      leftSection={
        <span className={classes.iconSlot}>
          {testStatus === "success" ? (
            <StatusCheckIcon size={16} />
          ) : testStatus === "error" ? (
            <StatusXIcon size={16} />
          ) : (
            <TestConnectionIcon size={16} />
          )}
        </span>
      }
      onClick={onClick}
      loading={loading}
      disabled={disabled}
    >
      Test connection
    </Button>
  );
}
