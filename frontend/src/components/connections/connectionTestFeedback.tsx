import { Button } from "@mantine/core"

import classes from "src/components/connections/connectionTestFeedback.module.css"
import { StatusCheckIcon } from "src/components/connections/StatusCheckIcon"
import { StatusXIcon } from "src/components/connections/StatusXIcon"
import { TestConnectionIcon } from "src/components/connections/TestConnectionIcon"
import type { ConnectionTestStatus } from "src/components/connections/useConnectionTestFeedback"

export function TestConnectionButton({
  testStatus,
  loading,
  disabled,
  onClick,
}: {
  testStatus: ConnectionTestStatus
  loading?: boolean
  disabled?: boolean
  onClick: () => void
}) {
  return (
    <Button
      type="button"
      variant="light"
      classNames={{ root: classes.button, section: classes.section }}
      data-status={testStatus}
      leftSection={
        <span key={testStatus} className={[classes.iconSlot, testStatus !== "idle" ? classes.iconPop : ""].filter(Boolean).join(" ")}>
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
  )
}
