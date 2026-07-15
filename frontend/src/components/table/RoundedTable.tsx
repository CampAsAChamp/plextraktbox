import { Paper, ScrollArea, Table, type TableProps } from "@mantine/core";
import type { ReactNode } from "react";

type RoundedTableProps = TableProps & {
  children: ReactNode;
  /** Shrink the frame to the table width (schedule preview, etc.). */
  fitContent?: boolean;
};

/**
 * Round bordered shell around a Mantine table.
 * Softens tables into the cinema-night baseline without pill-shaping every row.
 * Non-fitContent tables scroll horizontally on narrow viewports.
 */
export function RoundedTable({
  children,
  fitContent = false,
  style,
  ...props
}: RoundedTableProps) {
  const table = (
    <Table horizontalSpacing="md" verticalSpacing="sm" style={style} {...props}>
      {children}
    </Table>
  );

  return (
    <Paper
      withBorder
      radius="lg"
      style={{ overflow: "hidden", width: fitContent ? "fit-content" : undefined }}
    >
      {fitContent ? (
        table
      ) : (
        <ScrollArea type="scroll" offsetScrollbars scrollbarSize={8}>
          {table}
        </ScrollArea>
      )}
    </Paper>
  );
}
