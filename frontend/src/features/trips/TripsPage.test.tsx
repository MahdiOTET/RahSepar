import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ToastProvider } from "../../app/ToastContext";
import type { Ticket } from "../../types/api";
import TripsPage from "./TripsPage";

const { apiGetMock, loadInitialTicketsMock, loadRoutesMock } = vi.hoisted(
  () => ({
    apiGetMock: vi.fn(),
    loadInitialTicketsMock: vi.fn(),
    loadRoutesMock: vi.fn(),
  }),
);

vi.mock("../../app/AuthContext", () => ({
  useAuth: () => ({
    user: null,
    refreshUser: vi.fn(() => Promise.resolve(null)),
  }),
}));

vi.mock("../../lib/catalog", () => ({
  loadRoutes: loadRoutesMock,
  loadInitialTickets: loadInitialTicketsMock,
  invalidateInitialTickets: vi.fn(),
}));

vi.mock("../../lib/api", async () => {
  const actual =
    await vi.importActual<typeof import("../../lib/api")>("../../lib/api");
  return {
    ...actual,
    api: {
      ...actual.api,
      get: apiGetMock,
    },
  };
});

const routes = [
  { id: 1, origin: "تهران", destination: "شیراز" },
  { id: 2, origin: "شیراز", destination: "تهران" },
];

const tickets: Ticket[] = [
  {
    trip_id: 41,
    origin: "تهران",
    destination: "شیراز",
    departure_time: "2035-01-01T08:00:00Z",
    arrival_time: "2035-01-01T16:00:00Z",
    price: "1000000.00",
    bus_model: "Volvo B9R",
    capacity: 40,
    available_seats: 39,
  },
  {
    trip_id: 42,
    origin: "تهران",
    destination: "شیراز",
    departure_time: "2035-01-01T12:00:00Z",
    arrival_time: "2035-01-01T20:00:00Z",
    price: "1200000.00",
    bus_model: "Scania Maral",
    capacity: 44,
    available_seats: 30,
  },
];

function renderTrips() {
  return render(
    <ToastProvider>
      <MemoryRouter>
        <TripsPage />
      </MemoryRouter>
    </ToastProvider>,
  );
}

describe("TripsPage route search", () => {
  beforeEach(() => {
    apiGetMock.mockReset();
    loadRoutesMock.mockReset().mockResolvedValue(routes);
    loadInitialTicketsMock.mockReset().mockResolvedValue([]);
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  it("swaps a selected origin and destination", async () => {
    renderTrips();

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

  it("requests departure sorting and announces the updated result count", async () => {
    apiGetMock.mockResolvedValue([tickets[0]]);
    renderTrips();

    const sort = await screen.findByLabelText("مرتب‌سازی سفرها");
    await waitFor(() => expect(sort).toBeEnabled());
    fireEvent.change(sort, { target: { value: "departure_desc" } });

    await waitFor(() =>
      expect(apiGetMock).toHaveBeenCalledWith(
        expect.stringContaining("sort=departure_desc"),
      ),
    );
    expect(await screen.findByText("۱ سفر در دسترس")).toHaveAttribute(
      "aria-live",
      "polite",
    );
  });

  it("scrolls to off-screen search results but not when sorting them", async () => {
    apiGetMock.mockResolvedValue(tickets);
    renderTrips();

    const origin = screen.getByLabelText("مبدأ");
    const destination = screen.getByLabelText("مقصد");
    await waitFor(() => expect(origin).toBeEnabled());

    const resultsHeading = screen
      .getByRole("heading", { name: "سفرهای پیش رو" })
      .closest<HTMLElement>(".trip-results__heading");
    expect(resultsHeading).not.toBeNull();
    const scrollIntoView = vi.fn();
    resultsHeading!.scrollIntoView = scrollIntoView;
    vi.spyOn(resultsHeading!, "getBoundingClientRect").mockReturnValue({
      bottom: 1040,
      height: 240,
      left: 0,
      right: 800,
      top: 800,
      width: 800,
      x: 0,
      y: 800,
      toJSON: () => undefined,
    });

    fireEvent.change(origin, { target: { value: "تهران" } });
    fireEvent.change(destination, { target: { value: "شیراز" } });
    fireEvent.click(screen.getByRole("button", { name: "جست‌وجوی سفر" }));

    await waitFor(() =>
      expect(scrollIntoView).toHaveBeenCalledWith({
        behavior: "smooth",
        block: "start",
      }),
    );

    const sort = screen.getByLabelText("مرتب‌سازی سفرها");
    fireEvent.change(sort, { target: { value: "price_desc" } });
    await waitFor(() => expect(apiGetMock).toHaveBeenCalledTimes(2));
    expect(scrollIntoView).toHaveBeenCalledTimes(1);
  });

  it("reveals each visible card once with a single observer", async () => {
    loadInitialTicketsMock.mockResolvedValue(tickets);
    let intersectionCallback: IntersectionObserverCallback | undefined;
    let observerInstance: IntersectionObserver | undefined;
    let observerCount = 0;
    const observe = vi.fn();
    const unobserve = vi.fn();
    const disconnect = vi.fn();

    class IntersectionObserverMock implements IntersectionObserver {
      readonly root = null;
      readonly rootMargin = "0px 0px -8% 0px";
      readonly scrollMargin = "0px";
      readonly thresholds = [0.12];

      constructor(callback: IntersectionObserverCallback) {
        intersectionCallback = callback;
        observerInstance = this;
        observerCount += 1;
      }

      disconnect = disconnect;
      observe = observe;
      takeRecords = () => [];
      unobserve = unobserve;
    }

    vi.stubGlobal("IntersectionObserver", IntersectionObserverMock);

    const { container } = renderTrips();

    await waitFor(() => expect(observe).toHaveBeenCalledTimes(2));
    expect(observerCount).toBe(1);
    const revealItems =
      container.querySelectorAll<HTMLElement>(".trip-card-reveal");
    const firstItem = revealItems[0];
    expect(firstItem).toBeDefined();

    intersectionCallback?.(
      [
        {
          isIntersecting: true,
          target: firstItem,
        } as unknown as IntersectionObserverEntry,
      ],
      observerInstance as IntersectionObserver,
    );

    expect(firstItem).toHaveClass("trip-card-reveal--visible");
    expect(unobserve).toHaveBeenCalledOnce();
    expect(unobserve).toHaveBeenCalledWith(firstItem);
  });

  it("keeps cards static when reduced motion is requested", async () => {
    loadInitialTicketsMock.mockResolvedValue([tickets[0]]);
    const IntersectionObserverMock = vi.fn();
    vi.stubGlobal("IntersectionObserver", IntersectionObserverMock);
    vi.spyOn(window, "matchMedia").mockImplementation((query) => ({
      matches: query === "(prefers-reduced-motion: reduce)",
      media: query,
      onchange: null,
      addListener: () => undefined,
      removeListener: () => undefined,
      addEventListener: () => undefined,
      removeEventListener: () => undefined,
      dispatchEvent: () => false,
    }));

    const { container } = renderTrips();

    await screen.findByText("Volvo B9R");
    expect(IntersectionObserverMock).not.toHaveBeenCalled();
    expect(container.querySelector(".trip-list--reveal-ready")).toBeNull();
  });
});
