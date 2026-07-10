import { screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, test, vi } from "vitest";
import { App } from "./App";
import { renderWithProviders } from "./test/render";

function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

beforeEach(() => {
  vi.stubGlobal("fetch", vi.fn());
});

afterEach(() => {
  vi.unstubAllGlobals();
});

test("redirects to setup when no user exists", async () => {
  vi.mocked(fetch)
    .mockResolvedValueOnce(jsonResponse({ needs_setup: true }))
    .mockResolvedValueOnce(jsonResponse({ status: "ok", version: "0.1.0" }));

  renderWithProviders(<App />);

  await waitFor(() => {
    expect(screen.getByText("Welcome to plextraktbox")).toBeInTheDocument();
  });
});

test("shows login when setup is complete and session is absent", async () => {
  vi.mocked(fetch)
    .mockResolvedValueOnce(jsonResponse({ needs_setup: false }))
    .mockResolvedValueOnce(jsonResponse({ detail: "Not authenticated" }, 401));

  renderWithProviders(<App />);

  await waitFor(() => {
    expect(screen.getByRole("heading", { name: "Sign in" })).toBeInTheDocument();
  });
});

test("shows dashboard when setup is complete and session is present", async () => {
  vi.mocked(fetch)
    .mockResolvedValueOnce(jsonResponse({ needs_setup: false }))
    .mockResolvedValueOnce(
      jsonResponse({ id: 1, username: "nick", email: "nick@example.com" }),
    )
    .mockResolvedValueOnce(jsonResponse({ status: "ok", version: "0.1.0" }));

  renderWithProviders(<App />);

  await waitFor(() => {
    expect(screen.getByRole("heading", { name: "Dashboard" })).toBeInTheDocument();
    expect(screen.getByText(/Signed in as/)).toBeInTheDocument();
  });
});
