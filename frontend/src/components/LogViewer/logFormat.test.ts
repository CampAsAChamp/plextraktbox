import { describe, expect, it } from "vitest";
import {
  formatContextValue,
  formatContextValueCompact,
  formatLogDisplayMessage,
  hasExpandableContext,
  isJsonLikeString,
  logContextForDisplay,
  shouldPrettyPrintContextValue,
  shouldRenderStatusBadge,
  shouldSyntaxHighlightContextValue,
} from "src/components/LogViewer/logFormat";

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

  it("ignores message when it is the only display field", () => {
    expect(hasExpandableContext({ message: "Fetching ratings from letterboxd" })).toBe(false);
    expect(
      hasExpandableContext({ message: "Fetching ratings", source: "letterboxd" }),
    ).toBe(true);
  });
});

describe("formatLogDisplayMessage", () => {
  it("prefers context message when present", () => {
    expect(
      formatLogDisplayMessage({
        id: 1,
        run_id: 1,
        ts: "2026-01-01T00:00:00Z",
        level: "info",
        logger: "sync",
        message: "sync.fetch.start",
        context: { message: "Fetching ratings from letterboxd" },
      }),
    ).toBe("Fetching ratings from letterboxd");
  });

  it("falls back to event name", () => {
    expect(
      formatLogDisplayMessage({
        id: 1,
        run_id: 1,
        ts: "2026-01-01T00:00:00Z",
        level: "info",
        logger: "sync",
        message: "sync.run.complete",
        context: {},
      }),
    ).toBe("sync.run.complete");
  });
});

describe("logContextForDisplay", () => {
  it("drops message when used as display text", () => {
    expect(
      logContextForDisplay({ message: "Fetching ratings", source: "letterboxd" }),
    ).toEqual({ source: "letterboxd" });
  });
});

describe("shouldSyntaxHighlightContextValue", () => {
  it("highlights structured values", () => {
    expect(shouldSyntaxHighlightContextValue({ matched: 1 })).toBe(true);
    expect(shouldSyntaxHighlightContextValue("plain text")).toBe(false);
    expect(shouldSyntaxHighlightContextValue('{"a":1}')).toBe(true);
  });
});
