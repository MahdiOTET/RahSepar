import { useEffect, useState } from "react";
import { CalendarClock, CircleX, MapPin, TicketCheck } from "lucide-react";
import { Link } from "react-router-dom";

import { useAuth } from "../../app/AuthContext";
import { EmptyState } from "../../components/EmptyState";
import { LoadingState } from "../../components/LoadingState";
import { StatusMessage } from "../../components/StatusMessage";
import { api } from "../../lib/api";
import {
  bookingStatusLabel,
  formatDateTime,
  formatNumber,
  formatPrice,
  toPersianError,
} from "../../lib/format";
import type { BookingCancellation, BookingListItem } from "../../types/api";

export default function BookingsPage() {
  const { refreshUser } = useAuth();
  const [bookings, setBookings] = useState<BookingListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [cancelling, setCancelling] = useState<number | null>(null);
  const [confirming, setConfirming] = useState<number | null>(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  useEffect(() => {
    let active = true;
    api
      .get<BookingListItem[]>("/bookings", true)
      .then((result) => {
        if (active) setBookings(result);
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

  const cancelBooking = async (bookingId: number) => {
    setCancelling(bookingId);
    setError("");
    try {
      const result = await api.delete<BookingCancellation>(
        `/bookings/${bookingId}`,
        true,
      );
      setBookings((current) =>
        current.map((booking) =>
          booking.id === bookingId
            ? {
                ...booking,
                status: "cancelled",
                cancelled_at: result.cancelled_at,
              }
            : booking,
        ),
      );
      setNotice(
        `رزرو شماره ${formatNumber(bookingId)} لغو و مبلغ آن به کیف پول بازگردانده شد.`,
      );
      setConfirming(null);
      await refreshUser();
    } catch (reason) {
      setError(toPersianError(reason));
    } finally {
      setCancelling(null);
    }
  };

  return (
    <div className="bookings-page page-container">
      <header className="page-title">
        <span className="eyebrow">رزروهای من</span>
        <h1>همه سفرهای شما</h1>
        <p>جزئیات سفر، شماره صندلی و وضعیت هر رزرو را اینجا ببینید.</p>
      </header>

      {notice && <StatusMessage type="success">{notice}</StatusMessage>}
      {error && <StatusMessage type="error">{error}</StatusMessage>}

      {loading ? (
        <LoadingState label="در حال دریافت رزروها…" />
      ) : bookings.length === 0 ? (
        <EmptyState
          icon={TicketCheck}
          title="هنوز سفری رزرو نکرده‌اید"
          description="سفر مناسب را پیدا کنید و صندلی دلخواهتان را انتخاب کنید."
          action={
            <Link className="button button--primary" to="/">
              مشاهده سفرها
            </Link>
          }
        />
      ) : (
        <div className="booking-list">
          {bookings.map((booking) => {
            const canCancel =
              booking.status === "confirmed" &&
              new Date(booking.departure_time) > new Date();
            return (
              <article className="booking-card" key={booking.id}>
                <div className="booking-card__route">
                  <span className="booking-card__icon">
                    <MapPin size={21} />
                  </span>
                  <div>
                    <h2>
                      {booking.origin} به {booking.destination}
                    </h2>
                    <span>
                      <CalendarClock size={16} />{" "}
                      {formatDateTime(booking.departure_time)}
                    </span>
                  </div>
                  <span
                    className={`status-badge status-badge--${booking.status}`}
                  >
                    {bookingStatusLabel(booking.status)}
                  </span>
                </div>
                <dl className="booking-card__details">
                  <div>
                    <dt>شماره رزرو</dt>
                    <dd>{formatNumber(booking.id)}</dd>
                  </div>
                  <div>
                    <dt>شماره صندلی</dt>
                    <dd>{formatNumber(booking.seat_number)}</dd>
                  </div>
                  <div>
                    <dt>اتوبوس</dt>
                    <dd>{booking.bus_model ?? "بین‌شهری"}</dd>
                  </div>
                  <div>
                    <dt>مبلغ پرداختی</dt>
                    <dd>{formatPrice(booking.paid_price)}</dd>
                  </div>
                </dl>

                {canCancel && (
                  <div className="booking-card__actions">
                    {confirming === booking.id ? (
                      <div className="inline-confirm" role="alert">
                        <span>از لغو این رزرو مطمئن هستید؟</span>
                        <button
                          className="button button--danger"
                          type="button"
                          disabled={cancelling === booking.id}
                          onClick={() => void cancelBooking(booking.id)}
                        >
                          {cancelling === booking.id
                            ? "در حال لغو…"
                            : "بله، لغو شود"}
                        </button>
                        <button
                          className="button button--ghost"
                          type="button"
                          onClick={() => setConfirming(null)}
                        >
                          بازگشت
                        </button>
                      </div>
                    ) : (
                      <button
                        className="button button--danger-ghost"
                        type="button"
                        onClick={() => setConfirming(booking.id)}
                      >
                        <CircleX size={18} /> لغو رزرو
                      </button>
                    )}
                  </div>
                )}
              </article>
            );
          })}
        </div>
      )}
    </div>
  );
}
