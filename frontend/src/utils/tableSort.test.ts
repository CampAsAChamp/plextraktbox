import { describe, expect, it } from "vitest"

import { compareValues, nextSortState, sortRows } from "src/utils/tableSort"

describe("nextSortState", () => {
  it("cycles none → asc → desc → none", () => {
    expect(nextSortState(null, "name")).toEqual({ column: "name", direction: "asc" })
    expect(nextSortState({ column: "name", direction: "asc" }, "name")).toEqual({
      column: "name",
      direction: "desc",
    })
    expect(nextSortState({ column: "name", direction: "desc" }, "name")).toBeNull()
  })

  it("starts ascending when switching columns", () => {
    expect(nextSortState({ column: "status", direction: "desc" }, "name")).toEqual({
      column: "name",
      direction: "asc",
    })
  })
})

describe("compareValues", () => {
  it("compares strings, numbers, and booleans", () => {
    expect(compareValues("b", "a")).toBeGreaterThan(0)
    expect(compareValues(2, 10)).toBeLessThan(0)
    expect(compareValues(false, true)).toBeLessThan(0)
  })

  it("puts nullish values last", () => {
    expect(compareValues(null, "a")).toBeGreaterThan(0)
    expect(compareValues(undefined, 1)).toBeGreaterThan(0)
    expect(compareValues(null, undefined)).toBe(0)
  })
})

describe("sortRows", () => {
  type Row = { id: number; name: string; flag: boolean }
  type Column = "id" | "name" | "flag"

  const rows: Row[] = [
    { id: 2, name: "Beta", flag: false },
    { id: 1, name: "Alpha", flag: true },
    { id: 3, name: "alpha", flag: false },
  ]
  const getters: Record<Column, (row: Row) => string | number | boolean> = {
    id: (row) => row.id,
    name: (row) => row.name,
    flag: (row) => row.flag,
  }

  it("returns a copy when unsorted", () => {
    const sorted = sortRows(rows, null, getters)
    expect(sorted).toEqual(rows)
    expect(sorted).not.toBe(rows)
  })

  it("sorts by column and direction", () => {
    expect(sortRows(rows, { column: "name", direction: "asc" }, getters).map((row) => row.name)).toEqual(["Alpha", "alpha", "Beta"])

    expect(sortRows(rows, { column: "id", direction: "desc" }, getters).map((row) => row.id)).toEqual([3, 2, 1])
  })
})
