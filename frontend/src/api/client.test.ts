import { describe, expect, it } from "vitest";
import { formatApiDetail } from "src/api/client";

describe("formatApiDetail", () => {
  it("returns string detail as-is", () => {
    expect(formatApiDetail("Not authenticated", "Bad Request")).toBe("Not authenticated");
  });

  it("formats FastAPI 422 validation arrays", () => {
    const detail = [
      { loc: ["body", "cron"], msg: "Invalid cron expression", type: "value_error" },
      { loc: ["body", "name"], msg: "Field required", type: "missing" },
    ];
    expect(formatApiDetail(detail, "Unprocessable Entity")).toBe(
      "cron: Invalid cron expression; name: Field required",
    );
  });

  it("falls back when detail is empty", () => {
    expect(formatApiDetail(undefined, "Bad Request")).toBe("Bad Request");
    expect(formatApiDetail([], "Bad Request")).toBe("Bad Request");
  });

  it("stringifies unexpected object detail", () => {
    expect(formatApiDetail({ code: "x" }, "fallback")).toBe('{"code":"x"}');
  });
});
