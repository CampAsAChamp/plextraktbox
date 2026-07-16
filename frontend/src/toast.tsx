import { type NotificationData, notifications } from "@mantine/notifications"
import type { ReactNode } from "react"

function ToastIcon({ children, size = 18 }: { children: ReactNode; size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden
    >
      {children}
    </svg>
  )
}

function CheckIcon() {
  return (
    <ToastIcon>
      <polyline points="20 6 9 17 4 12" />
    </ToastIcon>
  )
}

function XIcon() {
  return (
    <ToastIcon>
      <line x1="18" y1="6" x2="6" y2="18" />
      <line x1="6" y1="6" x2="18" y2="18" />
    </ToastIcon>
  )
}

function AlertIcon() {
  return (
    <ToastIcon>
      <path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
      <line x1="12" y1="9" x2="12" y2="13" />
      <line x1="12" y1="17" x2="12.01" y2="17" />
    </ToastIcon>
  )
}

function InfoIcon() {
  return (
    <ToastIcon>
      <circle cx="12" cy="12" r="10" />
      <line x1="12" y1="16" x2="12" y2="12" />
      <line x1="12" y1="8" x2="12.01" y2="8" />
    </ToastIcon>
  )
}

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
