import classes from "src/components/table/SortableTh.module.css"
import type { SortState } from "src/utils/tableSort"

/** Class for body cells that belong to the active sort column. */
export function sortedColumnCellClass<TColumn extends string>(sort: SortState<TColumn> | null, column: TColumn): string | undefined {
  return sort?.column === column ? classes.sortedCell : undefined
}
