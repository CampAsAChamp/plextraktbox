import { describe, expect, it, vi } from "vitest";
import {
  SAVED_SECRET_PLACEHOLDER,
  secretPlaceholderHandlers,
  secretPlaceholderInputProps,
} from "src/components/connections/connectionFormHelpers";

describe("secretPlaceholderInputProps", () => {
  it("shows saved bullets and hides the visibility toggle", () => {
    const props = secretPlaceholderInputProps(
      SAVED_SECRET_PLACEHOLDER,
      vi.fn(),
      true,
      "Saved password hidden",
      "Saved on the server — enter a new password to replace it.",
    );

    expect(props.value).toBe(SAVED_SECRET_PLACEHOLDER);
    expect(props.placeholder).toBe("Saved password hidden");
    expect(props.description).toBe("Saved on the server — enter a new password to replace it.");
    expect(props.styles).toEqual({ visibilityToggle: { display: "none" } });
  });

  it("shows the visibility toggle and no saved description for edited secrets", () => {
    const props = secretPlaceholderInputProps(
      "new-password",
      vi.fn(),
      true,
      "Saved password hidden",
      "Saved on the server — enter a new password to replace it.",
    );

    expect(props.value).toBe("new-password");
    expect(props.description).toBeUndefined();
    expect(props.styles).toBeUndefined();
  });
});

describe("secretPlaceholderHandlers", () => {
  it("clears the saved placeholder on focus", () => {
    const setValue = vi.fn();
    const handlers = secretPlaceholderHandlers(SAVED_SECRET_PLACEHOLDER, setValue, true);

    handlers.onFocus();

    expect(setValue).toHaveBeenCalledWith("");
  });

  it("restores the saved placeholder on blur when empty", () => {
    const setValue = vi.fn();
    const handlers = secretPlaceholderHandlers("", setValue, true);

    handlers.onBlur();

    expect(setValue).toHaveBeenCalledWith(SAVED_SECRET_PLACEHOLDER);
  });
});
