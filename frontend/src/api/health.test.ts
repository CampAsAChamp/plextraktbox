import { describe, expect, it } from "vitest";
import { formatVersionLabel } from "./health";

describe("formatVersionLabel", () => {
  it("includes version only when git sha is absent", () => {
    expect(formatVersionLabel({ status: "ok", version: "1.2.3" })).toBe("v1.2.3");
  });

  it("includes short git sha when present", () => {
    expect(
      formatVersionLabel({ status: "ok", version: "1.2.3", git_sha: "abcdef123456" }),
    ).toBe("v1.2.3 · abcdef1");
  });

  it("shows connecting when health is undefined", () => {
    expect(formatVersionLabel(undefined)).toBe("connecting…");
  });
});
