import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import LoginPage from "./LoginPage";

const { loginMock } = vi.hoisted(() => ({
  loginMock: vi.fn(),
}));

vi.mock("../../app/AuthContext", () => ({
  useAuth: () => ({
    user: null,
    login: loginMock,
  }),
}));

function renderLogin(initialEntry = "/login") {
  return render(
    <MemoryRouter initialEntries={[initialEntry]}>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/bookings" element={<div>Passenger destination</div>} />
        <Route path="/manage" element={<div>Operator destination</div>} />
        <Route path="/account" element={<div>Requested destination</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("LoginPage demo accounts", () => {
  afterEach(cleanup);

  beforeEach(() => {
    loginMock.mockReset();
  });

  it("logs into the passenger account and opens booking history", async () => {
    loginMock.mockResolvedValue({});
    renderLogin();

    fireEvent.click(screen.getByRole("button", { name: /مسافر نمایشی/ }));

    expect(loginMock).toHaveBeenCalledWith("09800000001", "DevPass123!");
    expect(
      await screen.findByText("Passenger destination"),
    ).toBeInTheDocument();
  });

  it("logs into the operator account and honors a safe return path", async () => {
    loginMock.mockResolvedValue({});
    renderLogin("/login?returnTo=/account");

    fireEvent.click(screen.getByRole("button", { name: /اپراتور سامانه/ }));

    expect(loginMock).toHaveBeenCalledWith("09123456789", "DevPass123!");
    expect(
      await screen.findByText("Requested destination"),
    ).toBeInTheDocument();
  });

  it("disables every login path while a demo login is pending", () => {
    loginMock.mockReturnValue(new Promise(() => undefined));
    renderLogin();

    fireEvent.click(screen.getByRole("button", { name: /مسافر نمایشی/ }));

    expect(screen.getByLabelText("شماره موبایل")).toBeDisabled();
    expect(screen.getByLabelText("رمز عبور")).toBeDisabled();
    expect(screen.getByRole("button", { name: "در حال ورود…" })).toBeDisabled();
    expect(screen.getByRole("button", { name: /مسافر نمایشی/ })).toBeDisabled();
    expect(
      screen.getByRole("button", { name: /اپراتور سامانه/ }),
    ).toBeDisabled();
    expect(loginMock).toHaveBeenCalledTimes(1);
  });

  it("keeps demo credentials visible and reports authentication failure", async () => {
    loginMock.mockRejectedValue(new Error("Invalid Mobile or Password"));
    renderLogin();

    fireEvent.click(screen.getByRole("button", { name: /مسافر نمایشی/ }));

    await waitFor(() =>
      expect(screen.getByRole("alert")).toHaveTextContent(
        "شماره موبایل یا رمز عبور درست نیست.",
      ),
    );
    expect(screen.getByLabelText("شماره موبایل")).toHaveValue("09800000001");
    expect(screen.getByLabelText("رمز عبور")).toHaveValue("DevPass123!");
  });
});
