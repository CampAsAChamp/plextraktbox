import { afterEach, describe, expect, it, vi } from "vitest";
import { listThemes, updateActiveTheme, uploadTheme } from "./themes";

describe("themes api", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("lists themes", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => [{ id: "one-dark-pro", name: "Atom One Dark Pro", source: "builtin" }],
      }),
    );
    const themes = await listThemes();
    expect(themes[0]?.id).toBe("one-dark-pro");
  });

  it("updates active theme", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({ theme_id: "nord" }),
      }),
    );
    const result = await updateActiveTheme("nord");
    expect(result.theme_id).toBe("nord");
  });

  it("uploads theme css", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({ id: "ocean", name: "Ocean", source: "custom" }),
      }),
    );
    const info = await uploadTheme("/* @id: ocean */\nbody{}", "ocean.css");
    expect(info.source).toBe("custom");
  });
});
