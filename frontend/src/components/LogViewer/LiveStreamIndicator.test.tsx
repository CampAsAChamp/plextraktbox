import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { renderWithProviders } from "../../test/render";
import { LiveStreamAccent, LiveStreamIndicator } from "./LiveStreamIndicator";

describe("LiveStreamIndicator", () => {
  it("shows a pulsing live state while connected", () => {
    renderWithProviders(<LiveStreamIndicator connected ended={false} />);
    expect(screen.getByLabelText("Streaming logs live")).toHaveTextContent("Live");
  });

  it("shows connecting state before the stream is ready", () => {
    renderWithProviders(<LiveStreamIndicator connected={false} ended={false} />);
    expect(screen.getByLabelText("Connecting to log stream")).toHaveTextContent("Connecting");
  });

  it("shows complete state after the stream ends", () => {
    renderWithProviders(<LiveStreamIndicator connected={false} ended />);
    expect(screen.getByLabelText("Log stream complete")).toHaveTextContent("Complete");
  });
});

describe("LiveStreamAccent", () => {
  it("renders only while actively streaming", () => {
    renderWithProviders(<LiveStreamAccent connected ended={false} />);
    expect(screen.getByTestId("live-stream-accent")).toBeInTheDocument();
  });

  it("hides while connecting", () => {
    renderWithProviders(<LiveStreamAccent connected={false} ended={false} />);
    expect(screen.queryByTestId("live-stream-accent")).not.toBeInTheDocument();
  });

  it("hides after completion", () => {
    renderWithProviders(<LiveStreamAccent connected={false} ended />);
    expect(screen.queryByTestId("live-stream-accent")).not.toBeInTheDocument();
  });
});
