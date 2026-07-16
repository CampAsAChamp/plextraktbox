import { Button } from "@mantine/core"
import { useMutation } from "@tanstack/react-query"

import { ApiError } from "src/api/client"
import type { ConnectionSummary, Service } from "src/api/connections"
import { clearConnection } from "src/api/connectionsApi"
import { SERVICE_LABELS } from "src/components/connections/connectionStatus"
import { TrashIcon } from "src/components/icons/TrashIcon"
import { showToast } from "src/toast"

export function ClearConnectionButton({
  service,
  connection,
  onCleared,
  variant = "outline",
}: {
  service: Service
  connection: ConnectionSummary | undefined
  onCleared: () => void
  variant?: "subtle" | "outline"
}) {
  const clear = useMutation({
    mutationFn: () => clearConnection(service),
    onSuccess: () => {
      onCleared()
      showToast({
        color: "green",
        message: `${SERVICE_LABELS[service]} connection cleared`,
      })
    },
    onError: (error: unknown) => {
      showToast({
        color: "red",
        message: error instanceof ApiError ? String(error.message) : `Could not clear ${SERVICE_LABELS[service]} connection`,
      })
    },
  })

  if (!connection || connection.status === "unconfigured") return null

  function handleClear() {
    const confirmed = window.confirm(`Remove the saved ${SERVICE_LABELS[service]} connection? You will need to set it up again.`)
    if (confirmed) clear.mutate()
  }

  return (
    <Button variant={variant} color="red" leftSection={<TrashIcon />} onClick={handleClear} loading={clear.isPending} w="fit-content">
      Clear {SERVICE_LABELS[service]} connection
    </Button>
  )
}
