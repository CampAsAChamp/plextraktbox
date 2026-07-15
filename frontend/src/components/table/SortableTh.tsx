import { Group, Table, Text, UnstyledButton } from "@mantine/core";
import type { SortDirection, SortState } from "../../utils/tableSort";
import classes from "./SortableTh.module.css";

function ChevronUpIcon({ size = 16 }: { size?: number }) {
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
      <path d="M18 15l-6-6-6 6" />
    </svg>
  );
}

function ChevronUpDownIcon({ size = 16 }: { size?: number }) {
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
      <path d="M7 15l5 5 5-5" />
      <path d="M7 9l5-5 5 5" />
    </svg>
  );
}

function SortIndicator({ direction }: { direction?: SortDirection }) {
  const sorted = direction !== undefined;
  const className = [
    classes.indicator,
    sorted ? classes.indicatorSorted : "",
    direction === "desc" ? classes.indicatorDesc : "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <span className={className} aria-hidden>
      <span className={`${classes.layer} ${classes.idle}`}>
        <ChevronUpDownIcon />
      </span>
      <span className={`${classes.layer} ${classes.active}`}>
        <ChevronUpIcon />
      </span>
    </span>
  );
}

export function SortableTh<TColumn extends string>({
  column,
  label,
  sort,
  onSort,
  hiddenFrom,
}: {
  column: TColumn;
  label: string;
  sort: SortState<TColumn> | null;
  onSort: (column: TColumn) => void;
  /** Hide this column below the given Mantine breakpoint. */
  hiddenFrom?: "xs" | "sm" | "md" | "lg" | "xl";
}) {
  const active = sort?.column === column;
  const direction = active ? sort.direction : undefined;
  const ariaSort = active ? (direction === "asc" ? "ascending" : "descending") : "none";

  return (
    <Table.Th
      aria-sort={ariaSort}
      className={active ? `${classes.th} ${classes.thSorted}` : classes.th}
      hiddenFrom={hiddenFrom}
    >
      <UnstyledButton
        onClick={() => onSort(column)}
        aria-label={`Sort by ${label}`}
        style={{
          display: "block",
          width: "100%",
          color: "inherit",
          padding: "2px 0",
        }}
      >
        <Group gap={6} wrap="nowrap" justify="flex-start">
          <Text
            span
            size="sm"
            fw={700}
            className={`${classes.label}${active ? ` ${classes.labelSorted}` : ""}`}
            c={active ? "amber.2" : "inherit"}
          >
            {label}
          </Text>
          <SortIndicator direction={direction} />
        </Group>
      </UnstyledButton>
    </Table.Th>
  );
}

/** Class for body cells that belong to the active sort column. */
export function sortedColumnCellClass<TColumn extends string>(
  sort: SortState<TColumn> | null,
  column: TColumn,
): string | undefined {
  return sort?.column === column ? classes.sortedCell : undefined;
}
