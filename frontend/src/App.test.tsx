import { screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, test, vi } from "vitest";
import { App } from "./App";
import { renderWithProviders } from "./test/render";

beforeEach(() => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => new Response(JSON.stringify({ status: "ok", version: "0.1.0" }), { status: 200 })),
  );
});

afterEach(() => {
  vi.unstubAllGlobals();
});

test("renders the shell and shows API status once health resolves", async () => {
  renderWithProviders(<App />);
  expect(screen.getByText("plextraktbox")).toBeInTheDocument();
  await waitFor(() => expect(screen.getByText(/API ok/)).toBeInTheDocument());
});
