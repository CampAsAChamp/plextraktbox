import { ActionIcon, Tooltip } from "@mantine/core"
import { useClipboard } from "@mantine/hooks"

import { showToast } from "src/toast"

interface CopyActionProps {
  value: string
  label?: string
  size?: number
}

function CopyIcon({ size = 14 }: { size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden
    >
      <rect x="9" y="9" width="13" height="13" rx="2" />
      <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
    </svg>
  )
}

export function CopyAction({ value, label = "Copy", size = 14 }: CopyActionProps) {
  const clipboard = useClipboard({ timeout: 1500 })

  return (
    <Tooltip label={clipboard.copied ? "Copied" : label}>
      <ActionIcon
        variant="subtle"
        size="sm"
        aria-label={label}
        onClick={(event) => {
          event.preventDefault()
          event.stopPropagation()
          clipboard.copy(value)
          showToast({ color: "green", message: "Copied" })
        }}
      >
        <CopyIcon size={size} />
      </ActionIcon>
    </Tooltip>
  )
}
