import { describe, expect, it } from "vitest";
import { formatExcludeLines, parseExcludeLines } from "./settings";

describe("exclude id helpers", () => {
  it("parses lines and commas", () => {
    expect(parseExcludeLines("1\n2, 3\n")).toEqual(["1", "2", "3"]);
  });

  it("formats lines for textareas", () => {
    expect(formatExcludeLines(["a", "b"])).toBe("a\nb");
    expect(formatExcludeLines(undefined)).toBe("");
  });
});
