import {
  act,
  cleanup,
  fireEvent,
  render,
  screen,
} from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ToastProvider, useToast } from "./ToastContext";

function ToastHarness() {
  const { showToast } = useToast();

  return (
    <button type="button" onClick={() => showToast("رزرو با موفقیت ثبت شد.")}>
      نمایش اعلان
    </button>
  );
}

afterEach(() => {
  cleanup();
  vi.useRealTimers();
});

describe("ToastProvider", () => {
  it("shows a success message and dismisses it automatically", () => {
    vi.useFakeTimers();
    render(
      <ToastProvider>
        <ToastHarness />
      </ToastProvider>,
    );

    fireEvent.click(screen.getByRole("button", { name: "نمایش اعلان" }));
    expect(screen.getByRole("status")).toHaveTextContent(
      "رزرو با موفقیت ثبت شد.",
    );

    act(() => vi.advanceTimersByTime(4500));
    expect(screen.queryByTestId("toast")).not.toBeInTheDocument();
  });

  it("lets the user dismiss the message immediately", () => {
    render(
      <ToastProvider>
        <ToastHarness />
      </ToastProvider>,
    );

    fireEvent.click(screen.getByRole("button", { name: "نمایش اعلان" }));
    fireEvent.click(screen.getByRole("button", { name: "بستن اعلان" }));

    expect(screen.queryByTestId("toast")).not.toBeInTheDocument();
  });
});
