import { describe, expect, it } from "vitest";
import { tokenizeJsonText } from "src/components/LogViewer/ColoredJson";

describe("tokenizeJsonText", () => {
  it("colors keys, strings, numbers, and booleans", () => {
    const tokens = tokenizeJsonText('{\n  "matched": 1,\n  "dry_run": true\n}');

    expect(tokens).toContainEqual({ kind: "key", text: '"matched":' });
    expect(tokens).toContainEqual({ kind: "number", text: "1" });
    expect(tokens).toContainEqual({ kind: "key", text: '"dry_run":' });
    expect(tokens).toContainEqual({ kind: "boolean", text: "true" });
    expect(tokens).toContainEqual({ kind: "punctuation", text: "{" });
  });

  it("colors null and nested strings", () => {
    const tokens = tokenizeJsonText('{\n  "error": null,\n  "title": "Inception"\n}');

    expect(tokens).toContainEqual({ kind: "null", text: "null" });
    expect(tokens).toContainEqual({ kind: "string", text: '"Inception"' });
  });
});
