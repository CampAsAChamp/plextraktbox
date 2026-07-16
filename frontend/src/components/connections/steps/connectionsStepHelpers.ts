import type { ConnectionSummary } from "src/api/connections"
import classes from "src/pages/OnboardingStepper.module.css"

export const SERVICE_ORDER = ["plex", "trakt", "letterboxd", "tmdb"] as const

export function resolveActiveStep(connections: ConnectionSummary[]) {
  for (let index = 0; index < SERVICE_ORDER.length; index += 1) {
    const service = SERVICE_ORDER[index]
    const row = connections.find((item) => item.service === service)
    if (!row || row.status !== "ok") return index
  }
  return SERVICE_ORDER.length
}

export function allConnectionsOk(connections: ConnectionSummary[]) {
  return SERVICE_ORDER.every((service) => {
    const row = connections.find((item) => item.service === service)
    return row?.status === "ok"
  })
}

export function stepIconClass(connection: ConnectionSummary | undefined) {
  return connection?.status === "ok" ? `${classes.stepIcon} ${classes.stepIconConnected}` : classes.stepIcon
}
