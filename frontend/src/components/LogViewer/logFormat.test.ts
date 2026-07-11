import { describe, expect, it } from "vitest";
import {
  formatContextValue,
  formatContextValueCompact,
  hasExpandableContext,
  isJsonLikeString,
  shouldPrettyPrintContextValue,
  shouldRenderStatusBadge,
  shouldSyntaxHighlightContextValue,
} from "./logFormat";

describe("formatContextValue", () => {
  it("pretty-prints objects", () => {
    expect(formatContextValue({ matched: 1, added: 2 })).toBe(
      '{\n  "matched": 1,\n  "added": 2\n}',
    );
  });

  it("pretty-prints JSON strings", () => {
    expect(formatContextValue('{"status":"success"}')).toBe('{\n  "status": "success"\n}');
  });

  it("leaves plain strings unchanged", () => {
    expect(formatContextValue("would add Inception")).toBe("would add Inception");
  });
});

describe("isJsonLikeString", () => {
  it("detects object and array literals", () => {
    expect(isJsonLikeString('{"a":1}')).toBe(true);
    expect(isJsonLikeString("[1,2]")).toBe(true);
    expect(isJsonLikeString("not json")).toBe(false);
  });
});

describe("shouldPrettyPrintContextValue", () => {
  it("uses block layout for nested values", () => {
    expect(shouldPrettyPrintContextValue({ summary: { matched: 0 } })).toBe(true);
    expect(shouldPrettyPrintContextValue("short")).toBe(false);
  });
});

describe("shouldRenderStatusBadge", () => {
  it("matches known run status values", () => {
    expect(shouldRenderStatusBadge("status", "success")).toBe(true);
    expect(shouldRenderStatusBadge("status", "failed")).toBe(true);
    expect(shouldRenderStatusBadge("status", "pending")).toBe(false);
    expect(shouldRenderStatusBadge("state", "success")).toBe(false);
  });
});

describe("formatContextValueCompact", () => {
  it("renders compact JSON on one line", () => {
    expect(formatContextValueCompact({ matched: 1, added: 2 })).toBe('{"matched":1,"added":2}');
  });

  it("truncates long compact JSON", () => {
    const compact = formatContextValueCompact({ data: "x".repeat(200) }, 40);
    expect(compact.endsWith("…")).toBe(true);
    expect(compact.length).toBe(41);
  });
});

describe("hasExpandableContext", () => {
  it("is true when context has fields", () => {
    expect(hasExpandableContext({ status: "success" })).toBe(true);
    expect(hasExpandableContext({})).toBe(false);
  });
});

describe("shouldSyntaxHighlightContextValue", () => {
  it("highlights structured values", () => {
    expect(shouldSyntaxHighlightContextValue({ matched: 1 })).toBe(true);
    expect(shouldSyntaxHighlightContextValue("plain text")).toBe(false);
    expect(shouldSyntaxHighlightContextValue('{"a":1}')).toBe(true);
  });
});
