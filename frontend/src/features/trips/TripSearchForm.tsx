import { useMemo } from "react";
import { ArrowLeftRight, Search } from "lucide-react";

import type { RouteOption } from "../../types/api";

interface TripSearchFormProps {
  routes: RouteOption[];
  origin: string;
  destination: string;
  loading: boolean;
  onOriginChange: (origin: string) => void;
  onDestinationChange: (destination: string) => void;
  onSwap: () => void;
  onSearch: () => void;
}

function uniqueCities(cities: string[]): string[] {
  return [...new Set(cities)];
}

export function TripSearchForm({
  routes,
  origin,
  destination,
  loading,
  onOriginChange,
  onDestinationChange,
  onSwap,
  onSearch,
}: TripSearchFormProps) {
  const origins = useMemo(
    () => uniqueCities(routes.map((route) => route.origin)),
    [routes],
  );
  const destinations = useMemo(
    () =>
      uniqueCities(
        routes
          .filter((route) => !origin || route.origin === origin)
          .map((route) => route.destination),
      ),
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

  return (
    <form
      className="trip-search"
      onSubmit={(event) => {
        event.preventDefault();
        onSearch();
      }}
    >
      <div className="trip-search__field">
        <label htmlFor="origin">مبدأ</label>
        <select
          id="origin"
          value={origin}
          required
          onChange={(event) => onOriginChange(event.target.value)}
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
        onClick={onSwap}
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
          onChange={(event) => onDestinationChange(event.target.value)}
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
        disabled={loading}
      >
        <Search size={20} aria-hidden="true" />
        {loading ? "در حال جست‌وجو…" : "جست‌وجوی سفر"}
      </button>
    </form>
  );
}
