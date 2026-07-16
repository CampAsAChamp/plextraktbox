import { type MantineRadius, Paper, ScrollArea, Table, type TableProps } from "@mantine/core"
import type { ReactNode } from "react"

type RoundedTableProps = TableProps & {
  children: ReactNode
  /** Shrink the frame to the table width (schedule preview, etc.). */
  fitContent?: boolean
  /**
   * Minimum table width so columns scroll horizontally instead of compressing.
   * Ignored when `fitContent` is set. Defaults to 720 for list tables.
   */
  minWidth?: number | string
  /** Corner radius for the bordered shell. Defaults to `sm` when fitContent, else `lg`. */
  radius?: MantineRadius
}

/**
 * Round bordered shell around a Mantine table.
 * Softens tables into the cinema-night baseline without pill-shaping every row.
 * Non-fitContent tables scroll horizontally on narrow viewports.
 */
export function RoundedTable({ children, fitContent = false, minWidth = 720, radius, style, ...props }: RoundedTableProps) {
  const table = (
    <Table
      horizontalSpacing="md"
      verticalSpacing="sm"
      style={{
        ...style,
        ...(fitContent ? undefined : { minWidth }),
      }}
      {...props}
    >
      {children}
    </Table>
  )

  return (
    <Paper
      withBorder
      radius={radius ?? (fitContent ? "sm" : "lg")}
      style={{ overflow: "hidden", width: fitContent ? "fit-content" : undefined }}
    >
      {fitContent ? (
        table
      ) : (
        <ScrollArea type="auto" scrollbarSize={8}>
          {table}
        </ScrollArea>
      )}
    </Paper>
  )
}
