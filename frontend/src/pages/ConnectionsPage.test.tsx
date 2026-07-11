import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ConnectionsPage } from "./ConnectionsPage";
import classes from "./OnboardingStepper.module.css";
import { renderWithProviders } from "../test/render";

function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function connectionsPending() {
  return jsonResponse({
    needs_connections: true,
    connections: [
      { service: "plex", status: "unconfigured", config: {}, token_expires_at: null },
      { service: "trakt", status: "unconfigured", config: {}, token_expires_at: null },
      { service: "letterboxd", status: "unconfigured", config: {}, token_expires_at: null },
      { service: "tmdb", status: "unconfigured", config: {}, token_expires_at: null },
    ],
  });
}

function stepIconFor(label: string) {
  const step = screen.getByRole("button", { name: new RegExp(label, "i") });
  const icon = step.querySelector('[class*="stepIcon"]');
  if (!icon) {
    throw new Error(`Could not find step icon for ${label}`);
  }
  return icon;
}

beforeEach(() => {
  vi.stubGlobal("fetch", vi.fn());
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("ConnectionsPage stepper", () => {
  it("does not mark Plex as connected when jumping to Trakt before Plex is set up", async () => {
    const user = userEvent.setup();
    vi.mocked(fetch).mockResolvedValueOnce(connectionsPending());

    renderWithProviders(<ConnectionsPage />);

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Connect your services" })).toBeInTheDocument();
    });

    const traktStep = screen.getByRole("button", { name: /trakt/i });
    await user.click(traktStep);

    expect(screen.getByRole("button", { name: "Connect Trakt" })).toBeInTheDocument();
    expect(traktStep).toHaveAttribute("data-progress", "true");

    const plexIcon = stepIconFor("plex");
    expect(plexIcon.className).not.toContain(classes.stepIconConnected);
  });
});
