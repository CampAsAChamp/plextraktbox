export type SortDirection = "asc" | "desc"

export interface SortState<TColumn extends string> {
  column: TColumn
  direction: SortDirection
}

export type SortableValue = string | number | boolean | null | undefined

export function nextSortState<TColumn extends string>(current: SortState<TColumn> | null, column: TColumn): SortState<TColumn> | null {
  if (current?.column !== column) {
    return { column, direction: "asc" }
  }
  if (current.direction === "asc") {
    return { column, direction: "desc" }
  }
  return null
}

export function compareValues(a: SortableValue, b: SortableValue): number {
  const aMissing = a === null || a === undefined
  const bMissing = b === null || b === undefined
  if (aMissing && bMissing) {
    return 0
  }
  if (aMissing) {
    return 1
  }
  if (bMissing) {
    return -1
  }
  if (typeof a === "string" && typeof b === "string") {
    return a.localeCompare(b, undefined, { numeric: true, sensitivity: "base" })
  }
  if (typeof a === "boolean" && typeof b === "boolean") {
    return Number(a) - Number(b)
  }
  if (typeof a === "number" && typeof b === "number") {
    return a - b
  }
  return String(a).localeCompare(String(b), undefined, { numeric: true, sensitivity: "base" })
}

export function sortRows<T, TColumn extends string>(
  rows: readonly T[],
  sort: SortState<TColumn> | null,
  getters: Record<TColumn, (row: T) => SortableValue>,
): T[] {
  if (!sort) {
    return [...rows]
  }
  const getValue = getters[sort.column]
  const direction = sort.direction === "asc" ? 1 : -1
  return [...rows].sort((left, right) => compareValues(getValue(left), getValue(right)) * direction)
}
