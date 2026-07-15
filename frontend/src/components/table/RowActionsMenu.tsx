import { ActionIcon, Menu } from "@mantine/core";
import type { ReactNode } from "react";

function MoreIcon({ size = 18 }: { size?: number }) {
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
      <circle cx="12" cy="12" r="1" />
      <circle cx="12" cy="5" r="1" />
      <circle cx="12" cy="19" r="1" />
    </svg>
  );
}

type RowActionsMenuProps = {
  ariaLabel: string;
  children: ReactNode;
};

/** Touch-friendly labeled row actions (replaces tooltip-only ActionIcon strips). */
export function RowActionsMenu({ ariaLabel, children }: RowActionsMenuProps) {
  return (
    <Menu position="bottom-end" withinPortal width={200}>
      <Menu.Target>
        <ActionIcon
          variant="light"
          size="lg"
          miw={44}
          h={44}
          aria-label={ariaLabel}
        >
          <MoreIcon />
        </ActionIcon>
      </Menu.Target>
      <Menu.Dropdown>{children}</Menu.Dropdown>
    </Menu>
  );
}
