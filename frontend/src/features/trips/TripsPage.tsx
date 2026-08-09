import { useEffect, useMemo, useState } from "react";
import { ArrowLeftRight, BusFront, Search } from "lucide-react";
import { useNavigate } from "react-router-dom";

import { useAuth } from "../../app/AuthContext";
import { EmptyState } from "../../components/EmptyState";
import { LoadingState } from "../../components/LoadingState";
import { StatusMessage } from "../../components/StatusMessage";
import { api, toQueryString } from "../../lib/api";
import {
  invalidateInitialTickets,
  loadInitialTickets,
  loadRoutes,
} from "../../lib/catalog";
import { formatNumber, toPersianError } from "../../lib/format";
import type { BookingResult, RouteOption, Ticket } from "../../types/api";
import { SeatPicker } from "./SeatPicker";
import { TripCard } from "./TripCard";

type SortOrder = "price_asc" | "price_desc";

export default function TripsPage() {
  const navigate = useNavigate();
  const { user, refreshUser } = useAuth();
  const [routes, setRoutes] = useState<RouteOption[]>([]);
  const [origin, setOrigin] = useState("");
  const [destination, setDestination] = useState("");
  const [sort, setSort] = useState<SortOrder>("price_asc");
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [selectedTrip, setSelectedTrip] = useState<Ticket | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [searched, setSearched] = useState(false);

  useEffect(() => {
    let active = true;
    Promise.all([loadRoutes(), loadInitialTickets()])
      .then(([routeOptions, initialTickets]) => {
        if (!active) return;
        setRoutes(routeOptions);
        setTickets(initialTickets);
      })
      .catch((reason: unknown) => {
        if (active) setError(toPersianError(reason));
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  const origins = useMemo(
    () => [...new Set(routes.map((route) => route.origin))],
    [routes],
  );
  const destinations = useMemo(
    () => [
      ...new Set(
        routes
          .filter((route) => !origin || route.origin === origin)
          .map((route) => route.destination),
      ),
    ],
    [routes, origin],
  );
  const canSwap = useMemo(
    () =>
      Boolean(origin && destination) &&
      routes.some(
        (route) => route.origin === destination && route.destination === origin,
      ),
    [routes, origin, destination],
  );

  const fetchTickets = async (nextSort = sort) => {
    setLoading(true);
    setError("");
    try {
      const result = await api.get<Ticket[]>(
        `/tickets${toQueryString({ origin, destination, sort: nextSort, limit: 100 })}`,
      );
      setTickets(result);
      setSearched(Boolean(origin || destination));
    } catch (reason) {
      setError(toPersianError(reason));
    } finally {
      setLoading(false);
    }
  };

  const selectTrip = (trip: Ticket) => {
    if (!user) {
      navigate("/login?returnTo=/");
      return;
    }
    setSelectedTrip(trip);
  };

  const booked = async (booking: BookingResult) => {
    setSelectedTrip(null);
    setNotice(
      `رزرو شما با شماره ${formatNumber(booking.id)} با موفقیت ثبت شد.`,
    );
    invalidateInitialTickets();
    await Promise.all([fetchTickets(), refreshUser()]);
  };

  return (
    <div className="trips-page page-container">
      <section className="search-hero">
        <div className="search-hero__copy">
          <span className="eyebrow">سفر بعدی شما</span>
          <h1>کجا می‌خواهید بروید؟</h1>
          <p>
            مبدأ و مقصد را انتخاب کنید؛ راه‌سپار بهترین گزینه‌ها را بی‌درنگ نشان
            می‌دهد.
          </p>
        </div>

        <form
          className="trip-search"
          onSubmit={(event) => {
            event.preventDefault();
            void fetchTickets();
          }}
        >
          <div className="trip-search__field">
            <label htmlFor="origin">مبدأ</label>
            <select
              id="origin"
              value={origin}
              required
              onChange={(event) => {
                const nextOrigin = event.target.value;
                setOrigin(nextOrigin);
                const destinationStillValid = routes.some(
                  (route) =>
                    route.origin === nextOrigin &&
                    route.destination === destination,
                );
                if (!destinationStillValid) setDestination("");
              }}
            >
              <option value="">شهر مبدأ را انتخاب کنید</option>
              {origins.map((city) => (
                <option key={city} value={city}>
                  {city}
                </option>
              ))}
            </select>
          </div>
          <button
            className="trip-search__connector"
            type="button"
            disabled={!canSwap}
            aria-label="جابه‌جایی مبدأ و مقصد"
            onClick={() => {
              const previousOrigin = origin;
              setOrigin(destination);
              setDestination(previousOrigin);
            }}
          >
            <ArrowLeftRight size={20} aria-hidden="true" />
          </button>
          <div className="trip-search__field">
            <label htmlFor="destination">مقصد</label>
            <select
              id="destination"
              value={destination}
              required
              disabled={!origin}
              onChange={(event) => setDestination(event.target.value)}
            >
              <option value="">شهر مقصد را انتخاب کنید</option>
              {destinations.map((city) => (
                <option key={city} value={city}>
                  {city}
                </option>
              ))}
            </select>
          </div>
          <button
            className="button button--accent trip-search__submit"
            type="submit"
          >
            <Search size={20} aria-hidden="true" />
            جست‌وجوی سفر
          </button>
        </form>
      </section>

      {notice && <StatusMessage type="success">{notice}</StatusMessage>}
      {error && <StatusMessage type="error">{error}</StatusMessage>}

      <section className="trip-results" aria-labelledby="trip-results-title">
        <div className="section-heading">
          <div>
            <span className="eyebrow">
              {searched ? "نتیجه جست‌وجو" : "پیشنهادهای آماده"}
            </span>
            <h2 id="trip-results-title">
              {searched ? `${origin} به ${destination}` : "سفرهای پیش رو"}
            </h2>
            {!loading && <p>{formatNumber(tickets.length)} سفر در دسترس</p>}
          </div>
          <div className="segmented-control" aria-label="مرتب‌سازی قیمت">
            <button
              type="button"
              aria-pressed={sort === "price_asc"}
              onClick={() => {
                setSort("price_asc");
                void fetchTickets("price_asc");
              }}
            >
              ارزان‌ترین
            </button>
            <button
              type="button"
              aria-pressed={sort === "price_desc"}
              onClick={() => {
                setSort("price_desc");
                void fetchTickets("price_desc");
              }}
            >
              گران‌ترین
            </button>
          </div>
        </div>

        {loading ? (
          <LoadingState label="در حال یافتن سفرها…" />
        ) : tickets.length > 0 ? (
          <div className="trip-list">
            {tickets.map((trip) => (
              <TripCard key={trip.trip_id} trip={trip} onSelect={selectTrip} />
            ))}
          </div>
        ) : (
          <EmptyState
            icon={BusFront}
            title="برای این مسیر سفری پیدا نشد"
            description="مسیر دیگری را امتحان کنید یا کمی بعد دوباره برگردید."
          />
        )}
      </section>

      {selectedTrip && (
        <SeatPicker
          trip={selectedTrip}
          onClose={() => setSelectedTrip(null)}
          onBooked={(booking) => void booked(booking)}
        />
      )}
    </div>
  );
}
