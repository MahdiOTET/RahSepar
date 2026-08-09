import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { useAuth } from "../../app/AuthContext";
import { useToast } from "../../app/ToastContext";
import { StatusMessage } from "../../components/StatusMessage";
import { invalidateInitialTickets } from "../../lib/catalog";
import { formatNumber } from "../../lib/format";
import type { BookingResult, Ticket, TicketSort } from "../../types/api";
import { SeatPicker } from "./SeatPicker";
import { TripResults } from "./TripResults";
import { TripSearchForm } from "./TripSearchForm";
import { useConditionalResultScroll } from "./useConditionalResultScroll";
import { useTripCatalog } from "./useTripCatalog";

export default function TripsPage() {
  const navigate = useNavigate();
  const { user, refreshUser } = useAuth();
  const { showToast } = useToast();
  const [origin, setOrigin] = useState("");
  const [destination, setDestination] = useState("");
  const [sort, setSort] = useState<TicketSort>("price_asc");
  const [selectedTrip, setSelectedTrip] = useState<Ticket | null>(null);
  const {
    routes,
    tickets,
    loading,
    error,
    searched,
    resultRevision,
    loadTickets,
  } = useTripCatalog();
  const { headingRef, requestScroll } = useConditionalResultScroll(loading);

  const changeOrigin = (nextOrigin: string) => {
    setOrigin(nextOrigin);
    const destinationIsValid = routes.some(
      (route) =>
        route.origin === nextOrigin && route.destination === destination,
    );
    if (!destinationIsValid) setDestination("");
  };

  const swapRoute = () => {
    setOrigin(destination);
    setDestination(origin);
  };

  const searchTrips = async () => {
    const succeeded = await loadTickets({ origin, destination, sort });
    if (succeeded) requestScroll();
  };

  const changeSort = (nextSort: TicketSort) => {
    setSort(nextSort);
    void loadTickets({ origin, destination, sort: nextSort });
  };

  const selectTrip = (trip: Ticket) => {
    if (!user) {
      navigate("/login?returnTo=/");
      return;
    }
    setSelectedTrip(trip);
  };

  const completeBooking = async (booking: BookingResult) => {
    setSelectedTrip(null);
    showToast(
      `رزرو شماره ${formatNumber(booking.id)} با موفقیت ثبت شد و مبلغ آن از کیف پول پرداخت شد.`,
    );
    invalidateInitialTickets();
    await Promise.all([
      loadTickets({ origin, destination, sort }, { animate: false }),
      refreshUser(),
    ]);
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

        <TripSearchForm
          routes={routes}
          origin={origin}
          destination={destination}
          loading={loading}
          onOriginChange={changeOrigin}
          onDestinationChange={setDestination}
          onSwap={swapRoute}
          onSearch={() => void searchTrips()}
        />
      </section>

      {error && <StatusMessage type="error">{error}</StatusMessage>}

      <TripResults
        headingRef={headingRef}
        loading={loading}
        searched={searched}
        origin={origin}
        destination={destination}
        sort={sort}
        tickets={tickets}
        resultRevision={resultRevision}
        onSortChange={changeSort}
        onSelect={selectTrip}
      />

      {selectedTrip && (
        <SeatPicker
          trip={selectedTrip}
          onClose={() => setSelectedTrip(null)}
          onBooked={(booking) => void completeBooking(booking)}
        />
      )}
    </div>
  );
}
