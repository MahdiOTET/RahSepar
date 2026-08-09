import { act, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { hasSeenSplash, SplashScreen } from "./SplashScreen";

vi.mock("../lib/catalog", () => ({
  preloadHome: vi.fn(() => Promise.resolve([])),
}));

describe("SplashScreen", () => {
  beforeEach(() => {
    sessionStorage.clear();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("offers the release link and lets the user skip", () => {
    const onComplete = vi.fn();
    render(<SplashScreen onComplete={onComplete} />);

    expect(screen.getByText("راه‌سپار")).toBeInTheDocument();
    expect(screen.getByText("Developed by MahdiOTET")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /نسخه خط فرمان/ })).toHaveAttribute(
      "href",
      expect.stringContaining("releases/tag/v1.0.0"),
    );

    fireEvent.click(screen.getByRole("button", { name: /ورود به برنامه/ }));
    expect(onComplete).toHaveBeenCalledOnce();
    expect(hasSeenSplash()).toBe(true);
  });

  it("completes automatically after five seconds", () => {
    const onComplete = vi.fn();
    render(<SplashScreen onComplete={onComplete} />);

    act(() => vi.advanceTimersByTime(5_000));
    expect(onComplete).toHaveBeenCalledOnce();
    expect(hasSeenSplash()).toBe(true);
  });
});
