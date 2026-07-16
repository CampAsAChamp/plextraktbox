import { describe, expect, it } from "vitest";
import { isValidCronExpression } from "src/utils/cron";

describe("isValidCronExpression", () => {
  it("accepts standard 5-field cron expressions", () => {
    expect(isValidCronExpression("0 3 * * *")).toBe(true);
    expect(isValidCronExpression("  * * * * *  ")).toBe(true);
  });

  it("rejects invalid cron expressions", () => {
    expect(isValidCronExpression("")).toBe(false);
    expect(isValidCronExpression("invalid")).toBe(false);
    expect(isValidCronExpression("0 3 * *")).toBe(false);
    expect(isValidCronExpression("99 99 99 99 99")).toBe(false);
  });
});
