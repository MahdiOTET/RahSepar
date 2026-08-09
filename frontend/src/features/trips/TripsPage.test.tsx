import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import TripsPage from "./TripsPage";

vi.mock("../../app/AuthContext", () => ({
  useAuth: () => ({
    user: null,
    refreshUser: vi.fn(() => Promise.resolve(null)),
  }),
}));

vi.mock("../../lib/catalog", () => ({
  loadRoutes: vi.fn(() =>
    Promise.resolve([
      { id: 1, origin: "تهران", destination: "شیراز" },
      { id: 2, origin: "شیراز", destination: "تهران" },
    ]),
  ),
  loadInitialTickets: vi.fn(() => Promise.resolve([])),
  invalidateInitialTickets: vi.fn(),
}));

describe("TripsPage route search", () => {
  it("swaps a selected origin and destination", async () => {
    render(
      <MemoryRouter>
        <TripsPage />
      </MemoryRouter>,
    );

    const origin = screen.getByLabelText("مبدأ") as HTMLSelectElement;
    const destination = screen.getByLabelText("مقصد") as HTMLSelectElement;
    const swap = screen.getByRole("button", {
      name: "جابه‌جایی مبدأ و مقصد",
    });

    await waitFor(() => expect(origin.options).toHaveLength(3));
    expect(swap).toBeDisabled();

    fireEvent.change(origin, { target: { value: "تهران" } });
    fireEvent.change(destination, { target: { value: "شیراز" } });
    expect(swap).toBeEnabled();

    fireEvent.click(swap);
    expect(origin.value).toBe("شیراز");
    expect(destination.value).toBe("تهران");
  });
});
