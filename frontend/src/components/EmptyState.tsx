import type { ReactNode } from "react"

/** Dimmed empty-copy wrapper with a gentle fade-up entrance. */
export function EmptyState({ children }: { children: ReactNode }) {
  return <div className="ptbEmptyIn">{children}</div>
}
