import { fireEvent, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, expect, test, vi } from "vitest";
import { Route, Routes } from "react-router-dom";
import { renderWithProviders } from "../../test/render";
import { AppLayout } from "./AppLayout";

function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

beforeEach(() => {
  vi.stubGlobal("fetch", vi.fn());
  vi.mocked(fetch).mockResolvedValue(
    jsonResponse({
      status: "ok",
      version: "0.1.0",
      db_writable: true,
      scheduler_running: true,
    }),
  );

  // Treat viewport as below `sm` so Burger / Drawer are mounted.
  window.matchMedia = (query: string) => {
    const matches = query.includes("max-width");
    return {
      matches,
      media: query,
      onchange: null,
      addListener: () => undefined,
      removeListener: () => undefined,
      addEventListener: () => undefined,
      removeEventListener: () => undefined,
      dispatchEvent: () => false,
    };
  };
});

afterEach(() => {
  vi.unstubAllGlobals();
});

test("opens navigation drawer from burger and closes on navigate", async () => {
  renderWithProviders(
    <Routes>
      <Route
        element={<AppLayout username="nick" showLogout />}
      >
        <Route path="/" element={<div>Home page</div>} />
        <Route path="/jobs" element={<div>Jobs page</div>} />
      </Route>
    </Routes>,
  );

  const burger = await screen.findByRole("button", { name: "Open navigation" });
  fireEvent.click(burger);

  const drawer = await screen.findByRole("dialog");
  expect(drawer).toBeInTheDocument();

  fireEvent.click(
    within(drawer).getByRole("link", { name: "Jobs" }),
  );

  await waitFor(() => {
    expect(screen.getByText("Jobs page")).toBeInTheDocument();
  });
});

test("account menu links to the GitHub repo near version", async () => {
  const user = userEvent.setup();
  renderWithProviders(
    <Routes>
      <Route element={<AppLayout username="nick" showLogout />}>
        <Route path="/" element={<div>Home page</div>} />
      </Route>
    </Routes>,
  );

  await user.click(await screen.findByRole("button", { name: "Account menu" }));

  const github = await screen.findByRole("menuitem", { name: "GitHub" });
  expect(github).toHaveAttribute(
    "href",
    "https://github.com/CampAsAChamp/plextraktbox",
  );
  expect(github).toHaveAttribute("target", "_blank");
  expect(await screen.findByText("v0.1.0")).toBeInTheDocument();
});
