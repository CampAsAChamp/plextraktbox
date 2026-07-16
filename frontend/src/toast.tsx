import { type NotificationData, notifications } from "@mantine/notifications"
import type { ReactNode } from "react"

import { AlertIcon, CheckIcon, InfoIcon, XIcon } from "src/toastIcons"

/** Map Mantine toast colors to status icons. */
export function iconForToastColor(color: NotificationData["color"]): ReactNode {
  const name = typeof color === "string" ? color : "blue"
  switch (name) {
    case "green":
    case "teal":
      return <CheckIcon />
    case "red":
      return <XIcon />
    case "orange":
    case "yellow":
      return <AlertIcon />
    default:
      return <InfoIcon />
  }
}

/** Show a toast with color coding and a matching status icon. */
export function showToast(data: NotificationData) {
  const color = data.color ?? "blue"
  notifications.show({
    ...data,
    color,
    icon: data.icon ?? iconForToastColor(color),
  })
}
